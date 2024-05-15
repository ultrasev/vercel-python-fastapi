<p align="center">
 <img width="100px" src="public/vercel.png" align="center" alt="Deploy Python(+FastAPI) project on Vercel" />
 <h2 align="center">Deploy Python(+FastAPI) project on Vercel</h2>

<p align="center">
  <a href="https://github.com/ultrasev/vercel-python-fastapi/issues">
    <img alt="Issues" src="https://img.shields.io/github/issues/ultrasev/vercel-python-fastapi?style=flat&color=336791" />
  </a>
  <a href="https://github.com/ultrasev/vercel-python-fastapi/pulls">
    <img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr/ultrasev/vercel-python-fastapi?style=flat&color=336791" />
  </a>
  <br />
<a href="https://github.com/ultrasev/vercel-python-fastapi/issues/new/choose">Report Bug</a>
<a href="https://github.com/ultrasev/vercel-python-fastapi/issues/new/choose">Request Feature</a>
</p>


# Deploy with Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/ultrasev/vercel-python-fastapi/tree/master/vercel&demo-title=PythonDeployment&demo-description=Deploy&demo-url=https://llmproxy.vercel.app/&demo-image=https://vercel.com/button)

# Local Development

```bash
pip3 install -r requirements.txt
pip3 install uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

# Documentation
- [FastAPI framework](https://fastapi.tiangolo.com/)
- [Vercel: configure a build](https://dlj.one/ktkfme)
- [Stackoverflow: How can you specify python runtime version in vercel?](https://dlj.one/itw3m0)
- [Vercel Python hello world example](https://vercel.com/templates/python/python-hello-world)


# License
Copyright © 2024 [ultrasev](https://github.com/ultrasev).<br />
This project is [MIT](LICENSE) licensed.
