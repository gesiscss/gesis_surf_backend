# Web Tracker Backend

![GESIS](https://upload.wikimedia.org/wikipedia/commons/4/42/GESIS-Logo.svg)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)

Backend for GESIS Web Tracking services. By [Geomario](https://github.com/geomario).  
Questions? -> <mario.ramirez@gesis.org>

## Commands

Testing development inside Docker and running flake8 linting

```bsh
docker-compose run --rm app sh -c "flake8"
```

Testing service, up & running

```bsh
docker compose up -d
```

visit the service  
[backend service](127.0.0.1:8000)
