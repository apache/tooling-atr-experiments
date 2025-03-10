# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any

import aiofiles.os
import httpx
from quart import current_app, flash, render_template, request
from sqlmodel import select
from werkzeug.wrappers.response import Response

from asfquart.base import ASFQuartException
from asfquart.session import read as session_read
from atr.datasources.apache import (
    get_current_podlings_data,
    get_groups_data,
    get_ldap_projects_data,
)
from atr.db import create_async_db_session
from atr.db.models import (
    PMC,
    DistributionChannel,
    Package,
    PMCKeyLink,
    ProductLine,
    PublicSigningKey,
    Release,
    Task,
    VotePolicy,
)
from atr.db.service import get_pmcs

from . import blueprint


@blueprint.route("/performance")
async def admin_performance() -> str:
    """Display performance statistics for all routes."""
    from asfquart import APP

    if APP is ...:
        raise ASFQuartException("APP is not set", errorcode=500)

    # Read and parse the performance log file
    log_path = Path("route-performance.log")
    # # Show current working directory and its files
    # cwd = await asyncio.to_thread(Path.cwd)
    # await asyncio.to_thread(APP.logger.info, "Current working directory: %s", cwd)
    # iterable = await asyncio.to_thread(cwd.iterdir)
    # files = list(iterable)
    # await asyncio.to_thread(APP.logger.info, "Files in current directory: %s", files)
    if not await aiofiles.os.path.exists(log_path):
        await flash("No performance data currently available", "error")
        return await render_template("performance.html", stats=None)

    # Parse the log file and collect statistics
    stats = defaultdict(list)
    async with aiofiles.open(log_path) as f:
        async for line in f:
            try:
                _, _, _, methods, path, func, _, sync_ms, async_ms, total_ms = line.strip().split(" ")
                stats[path].append(
                    {
                        "methods": methods,
                        "function": func,
                        "sync_ms": int(sync_ms),
                        "async_ms": int(async_ms),
                        "total_ms": int(total_ms),
                        "timestamp": line.split(" - ")[0],
                    }
                )
            except (ValueError, IndexError):
                APP.logger.error("Error parsing line: %s", line)
                continue

    # Calculate summary statistics for each route
    summary = {}
    for path, timings in stats.items():
        total_times = [int(str(t["total_ms"])) for t in timings]
        sync_times = [int(str(t["sync_ms"])) for t in timings]
        async_times = [int(str(t["async_ms"])) for t in timings]

        summary[path] = {
            "count": len(timings),
            "methods": timings[0]["methods"],
            "function": timings[0]["function"],
            "total": {
                "mean": mean(total_times),
                "median": median(total_times),
                "min": min(total_times),
                "max": max(total_times),
                "stdev": stdev(total_times) if len(total_times) > 1 else 0,
            },
            "sync": {
                "mean": mean(sync_times),
                "median": median(sync_times),
                "min": min(sync_times),
                "max": max(sync_times),
            },
            "async": {
                "mean": mean(async_times),
                "median": median(async_times),
                "min": min(async_times),
                "max": max(async_times),
            },
            "last_timestamp": timings[-1]["timestamp"],
        }

    # Sort routes by average total time, descending
    def one_total_mean(x: tuple[str, dict]) -> float:
        return x[1]["total"]["mean"]

    sorted_summary = dict(sorted(summary.items(), key=one_total_mean, reverse=True))
    return await render_template("performance.html", stats=sorted_summary)


@blueprint.route("/data")
@blueprint.route("/data/<model>")
async def admin_data(model: str = "PMC") -> str:
    """Browse all records in the database."""

    # Map of model names to their classes
    models = {
        "PMC": PMC,
        "Release": Release,
        "Package": Package,
        "VotePolicy": VotePolicy,
        "ProductLine": ProductLine,
        "DistributionChannel": DistributionChannel,
        "PublicSigningKey": PublicSigningKey,
        "PMCKeyLink": PMCKeyLink,
        "Task": Task,
    }

    if model not in models:
        raise ASFQuartException(f"Model type '{model}' not found", 404)

    async with create_async_db_session() as db_session:
        # Get all records for the selected model
        statement = select(models[model])
        records = (await db_session.execute(statement)).scalars().all()

        # Convert records to dictionaries for JSON serialization
        records_dict = []
        for record in records:
            if hasattr(record, "dict"):
                record_dict = record.dict()
            else:
                # Fallback for models without dict() method
                record_dict = {
                    "id": getattr(record, "id", None),
                    "storage_key": getattr(record, "storage_key", None),
                }
                for key in record.__dict__:
                    if not key.startswith("_"):
                        record_dict[key] = getattr(record, key)
            records_dict.append(record_dict)

        return await render_template("data-browser.html", models=list(models.keys()), model=model, records=records_dict)


@blueprint.route("/projects/update", methods=["GET", "POST"])
async def admin_projects_update() -> str | Response | tuple[Mapping[str, Any], int]:
    """Update projects from remote data."""
    if request.method == "POST":
        try:
            updated_count = await _update_pmcs()
            return {
                "message": f"Successfully updated {updated_count} projects (PMCs and PPMCs) with membership data",
                "category": "success",
            }, 200
        except httpx.RequestError as e:
            return {
                "message": f"Failed to fetch data: {e!s}",
                "category": "error",
            }, 200
        except Exception as e:
            return {
                "message": f"Failed to update projects: {e!s}",
                "category": "error",
            }, 200

    # For GET requests, show the update form
    return await render_template("update-pmcs.html")


async def _update_pmcs() -> int:
    ldap_projects = await get_ldap_projects_data()
    podlings_data = await get_current_podlings_data()
    groups_data = await get_groups_data()

    updated_count = 0

    async with create_async_db_session() as db_session:
        async with db_session.begin():
            # First update PMCs
            for project in ldap_projects.projects:
                name = project.name
                # Skip non-PMC committees
                if not project.pmc:
                    continue

                # Get or create PMC
                statement = select(PMC).where(PMC.project_name == name)
                pmc = (await db_session.execute(statement)).scalar_one_or_none()
                if not pmc:
                    pmc = PMC(project_name=name)
                    db_session.add(pmc)

                # Update PMC data from groups.json
                pmc_members = groups_data.get(f"{name}-pmc")
                committers = groups_data.get(name)
                pmc.pmc_members = pmc_members if pmc_members is not None else []
                pmc.committers = committers if committers is not None else []
                # Ensure this is set for PMCs
                pmc.is_podling = False

                # For release managers, use PMC members for now
                # TODO: Consider a more sophisticated way to determine release managers
                #       from my POV, the list of release managers should be the list of people
                #       that have actually cut a release for that project
                pmc.release_managers = pmc.pmc_members

                updated_count += 1

            # Then add PPMCs (podlings)
            for podling_name, podling_data in podlings_data:
                # Get or create PPMC
                statement = select(PMC).where(PMC.project_name == podling_name)
                ppmc = (await db_session.execute(statement)).scalar_one_or_none()
                if not ppmc:
                    ppmc = PMC(project_name=podling_name)
                    db_session.add(ppmc)

                # Update PPMC data from groups.json
                ppmc.is_podling = True
                pmc_members = groups_data.get(f"{podling_name}-pmc")
                committers = groups_data.get(podling_name)
                ppmc.pmc_members = pmc_members if pmc_members is not None else []
                ppmc.committers = committers if committers is not None else []
                # Use PPMC members as release managers
                ppmc.release_managers = ppmc.pmc_members

                updated_count += 1

            # Add special entry for Tooling PMC
            # Not clear why, but it's not in the Whimsy data
            statement = select(PMC).where(PMC.project_name == "tooling")
            tooling_pmc = (await db_session.execute(statement)).scalar_one_or_none()
            if not tooling_pmc:
                tooling_pmc = PMC(project_name="tooling")
                db_session.add(tooling_pmc)
                updated_count += 1

            # Update Tooling PMC data
            # Could put this in the "if not tooling_pmc" block, perhaps
            tooling_pmc.pmc_members = ["wave", "tn", "sbp"]
            tooling_pmc.committers = ["wave", "tn", "sbp"]
            tooling_pmc.release_managers = ["wave"]
            tooling_pmc.is_podling = False

    return updated_count


@blueprint.route("/tasks")
async def admin_tasks() -> str:
    return await render_template("tasks.html")


@blueprint.route("/debug/database")
async def admin_debug_database() -> str:
    """Debug information about the database."""
    pmcs = await get_pmcs()
    return f"Database using {current_app.config['DATA_MODELS_FILE']} has {len(pmcs)} PMCs"


@blueprint.route("/keys/delete-all")
async def admin_keys_delete_all() -> str:
    """Debug endpoint to delete all of a user's keys."""
    session = await session_read()
    if session is None:
        raise ASFQuartException("Not authenticated", errorcode=401)

    async with create_async_db_session() as db_session:
        async with db_session.begin():
            # Get all keys for the user
            # TODO: Use session.apache_uid instead of session.uid?
            statement = select(PublicSigningKey).where(PublicSigningKey.apache_uid == session.uid)
            keys = (await db_session.execute(statement)).scalars().all()
            count = len(keys)

            # Delete all keys
            for key in keys:
                await db_session.delete(key)

        return f"Deleted {count} keys"
