![GESIS](https://www.google.com/url?sa=i&url=https%3A%2F%2Fde.m.wikipedia.org%2Fwiki%2FDatei%3AGESIS-Logo.svg&psig=AOvVaw3l0yR9sHGDXOX5b-OtAsH9&ust=1699103830837000&source=images&cd=vfe&ved=0CBIQjhxqFwoTCNC15JP1p4IDFQAAAAAdAAAAABAE)

# Web Tracker Backend

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
