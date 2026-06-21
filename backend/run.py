import uvicorn

if __name__ == "__main__":
    # The __main__ guard prevents Windows from infinitely spawning processes
    # when uvicorn's reloader or AI libraries attempt to use multiprocessing.
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
