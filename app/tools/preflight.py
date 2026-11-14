"""Local deployment preflight without creating cloud resources."""
import argparse
import json
from pathlib import Path
from app.services.readiness import readiness


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--deployment',action='store_true',help='Also require a strong workspace token and built UI')
    parser.add_argument('--frontend-dir',default=str(Path(__file__).resolve().parents[2]/'frontend/dist'))
    args=parser.parse_args(argv)
    result=readiness(require_token=args.deployment,frontend_dir=args.frontend_dir if args.deployment else None)
    print(json.dumps(result,indent=2))
    return 0 if result['ready'] else 1


if __name__=='__main__':
    raise SystemExit(main())
