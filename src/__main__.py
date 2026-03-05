import uvicorn
import argparse

# --------------------------------------------------------------------
#  __main__.py to Run Server in Production (with or without --reload)
# --------------------------------------------------------------------

# extract given arguments for the server environment, default to local (with reload)
def extract_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-e",
        "--env",
        type=str,
        help='Server environment. Either local, dev, or prod',
        choices=['dev', 'local', 'prod'],
        default='local'
    )

    args = arg_parser.parse_args()

    return {"env": args.env}

def main(env):
    print(f"- Running server for YouTube-Intelligence-Platform using Uvicorn -")
    uvicorn.run(
        app="src.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True if env == 'local' or env == 'dev' else False
    )

if __name__ == '__main__':
    args = extract_args()
    main(env=args['env'])
