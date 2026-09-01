from __future__ import annotations

import argparse
from datetime import date

from ..committees import CommitteeRegistry, MandateResolver
from ..core.models import ResearchSettings
from ..core.pipeline import ResearchPipeline
from ..persistence import Database
from ..sources import SourceCapabilityRegistry

def _settings(args: argparse.Namespace) -> ResearchSettings:
    links = list(args.extra_link or [])
    if args.extra_links:
        links.extend(line.strip() for line in open(args.extra_links, encoding="utf-8") if line.strip() and not line.startswith("#"))
    return ResearchSettings(committee=args.committee, agenda=args.agenda, portfolio=args.portfolio, freeze_date=date.fromisoformat(args.freeze_date) if args.freeze_date else None, background_guide=args.background_guide, research_notes=args.research_notes or "", extra_links=tuple(links), target_countries=tuple(args.target_countries or []), poi_count=args.poi_count, aggression=args.aggression, controversy=args.controversy, diplomacy=args.diplomacy, gemini_model=args.gemini_model, ollama_model=args.ollama_model)

def _add_research_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--committee", required=True); parser.add_argument("--agenda", required=True); parser.add_argument("--portfolio", required=True)
    parser.add_argument("--freeze-date"); parser.add_argument("--background-guide"); parser.add_argument("--research-notes"); parser.add_argument("--extra-links"); parser.add_argument("--extra-link", action="append")
    parser.add_argument("--target-countries", nargs="*"); parser.add_argument("--poi-count", type=int, default=10); parser.add_argument("--aggression", type=int, default=50); parser.add_argument("--controversy", type=int, default=50); parser.add_argument("--diplomacy", type=int, default=50); parser.add_argument("--gemini-model"); parser.add_argument("--ollama-model")

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="intelforge", description="Evidence-bound MUN tactical research engine")
    parser.add_argument("--database", default="intelforge.db")
    sub = parser.add_subparsers(dest="command", required=True)
    research = sub.add_parser("research", help="run the complete staged research pipeline"); _add_research_arguments(research)
    context = sub.add_parser("context", help="validate context and resolve mandate"); _add_research_arguments(context)
    sub.add_parser("committees", help="list registered committees"); sub.add_parser("sources", help="list source capabilities"); sub.add_parser("models", help="list configured Gemini models")
    for command in ("incidents", "legal", "generate", "validate", "export"):
        item = sub.add_parser(command, help=f"inspect persisted {command} artifacts")
        item.add_argument("job_id", type=int)
    status = sub.add_parser("status", help="show a persisted job"); status.add_argument("job_id", type=int)
    sub.add_parser("init", help="initialize SQLite storage")
    resume = sub.add_parser("resume", help="resume a blocked or failed job"); resume.add_argument("job_id", type=int)
    args = parser.parse_args(argv)
    if args.command == "committees":
        for item in CommitteeRegistry().all(): print(f"{item.id}: {item.official_name} ({', '.join(item.aliases)})")
        return 0
    if args.command == "sources":
        for item in SourceCapabilityRegistry().all(): print(f"{item['source_id']}: {item['access_method']} — {', '.join(item['capabilities'])}")
        return 0
    if args.command == "models":
        from ..models import GeminiModelRegistry
        models = GeminiModelRegistry().discover()
        print("\n".join(model.name for model in models) or "No Gemini models discovered; configure GEMINI_API_KEY.")
        return 0
    database = Database(args.database)
    if args.command == "init": print(f"Initialized {args.database}"); return 0
    if args.command == "status": print(database.status(args.job_id) or "Job not found"); return 0
    if args.command == "resume":
        job = database.status(args.job_id)
        if not job: print("Job not found"); return 1
        data = job["payload"]; data["freeze_date"] = date.fromisoformat(data["freeze_date"]) if data.get("freeze_date") else None; data["extra_links"] = tuple(data.get("extra_links", ())); data["target_countries"] = tuple(data.get("target_countries", ()))
        print(ResearchPipeline(database=database).run(ResearchSettings(**data), job_id=args.job_id)); return 0
    if args.command in {"incidents", "legal", "generate", "validate", "export"}:
        job = database.status(args.job_id)
        if not job: print("Job not found"); return 1
        if args.command == "generate":
            print("Generation is gated: run research first; only validated persisted candidate evidence packages can be generated.")
            return 2
        kind = {"incidents": "incidents", "legal": "legal", "validate": "validation", "export": "finalized"}[args.command]
        artifacts = database.artifacts(args.job_id, kind)
        if args.command == "export":
            print("\n\n".join(str(item["payload"]) for item in artifacts) or "No finalized POIs available for export.")
        else:
            print("\n".join(str(item["payload"]) for item in artifacts) or f"No persisted {kind} artifacts available.")
        return 0
    settings = _settings(args)
    if args.command == "context":
        print(MandateResolver(CommitteeRegistry()).resolve(settings.committee)); return 0
    result = ResearchPipeline(database=database).run(settings)
    print("╭──────────────────────────────────────────────╮\n│ IntelForge Tactical Research Engine          │\n╰──────────────────────────────────────────────╯")
    print(f"Committee: {settings.committee}\nAgenda: {settings.agenda}\nPortfolio: {settings.portfolio}\nFreeze Date: {settings.freeze_date or 'Not specified'}\n")
    for index, state in enumerate(result["stages"]): print(f"[{index}/18] {state['stage_id']:<28} {state['status']}")
    print(f"\nIncidents retained: {result['incidents']}\nEvidence claims: {result['evidence_claims']}\nLegal frameworks: {result['legal_frameworks']}\nFinal POIs: {len(result['final_pois'])}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
