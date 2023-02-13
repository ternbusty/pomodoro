from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from timer import Timer
from starlette.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/js", StaticFiles(directory="js"), name="js")
timer = Timer()


@app.get("/")
async def root():
    return FileResponse('index.html')


@app.get("/is_lazy/")
def is_lazy() -> bool:
    return timer.is_lazy


@app.get("/can_take_long_break/")
def can_take_long_break() -> bool:
    return timer.can_take_long_break


@app.get("/history/")
def history() -> str:
    return timer.get_history()


@app.get("/summary/")
def summary() -> str:
    return timer.summary_text


@app.get("/status/")
def get_status():
    return JSONResponse(content=timer.get_status())


@app.put("/summarize/")
def summarize() -> None:
    return timer.summarize()


@app.put("/terminate/")
def summarize() -> None:
    return timer.terminate()


@app.put("/start/")
async def start(background_tasks: BackgroundTasks, break_time: int = 0) -> None:
    background_tasks.add_task(timer.main, break_time)


@app.put("/start_break/")
def start_break(break_time: int = 0) -> None:
    timer.start_break(break_time)


@app.put("/start_long_break/")
def start_long_break(background_tasks: BackgroundTasks, break_time: int = 0) -> None:
    background_tasks.add_task(timer.start_long_break(break_time))


@app.put("/start_work/")
def start_work(task_name: str = "working") -> None:
    timer.start_work(task_name)
