"""Manual provider smoke check; never make paid calls during test discovery."""

if __name__ == "__main__":
    from app.services.llm.factory import get_llm

    print(get_llm().generate("Say hello."))
