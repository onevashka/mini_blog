from fastapi import FastAPI
from .auth.router import router as router_auth
from .api.router import router as router_blog
from .pages.router import router as frontend_router
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.include_router(router_auth)
app.include_router(router_blog)
app.include_router(frontend_router)
app.mount('/static', StaticFiles(directory='app/static'), name='static')


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', reload=True)