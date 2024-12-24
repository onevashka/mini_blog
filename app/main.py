from fastapi import FastAPI
from .auth.router import router as router_auth


app = FastAPI()
app.include_router(router_auth, prefix='/api')


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', reload=True)