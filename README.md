# GESIS Surf Backend

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

Running specific migrations

```bsh
docker-compose run --rm app sh -c "python manage.py makemigrations APP_NAME"
```

Specific testing

```bsh
docker-compose run --rm app sh -c "python manage.py test APP_NAME"
```

visit the service
[backend service](127.0.0.1:8000)

## Data Base Design

A database is a structured set of data held in a computer. For the backend of our tool, we will be using a PostgreSQL database; a relational database. A relational database is composed of tables and references. Describes entities and relationships between them, the Data is well-structured.

A relational database is suggested when the workload fits thousands of transactions per second. Our current participant's sample corresponds to ~400 users. The data at the same time needs to offer integrity. A relational database is highly structured and brings integrity. Additionally, the database needs to offer availability. Availability refers to the action of returning a response of the most actual data. Our department at CSS, need to have data access, consequently, working with a relational database grants complex query that express relationships in our tables.

Finally, the database is centralized and can be replicated asynchronously, such that we can offer accessibility to our data for social scientists.

> Relational Model was proposed by Edgar F Codd. The model structures data as entities and creates relationships with entities.

## Entity Relationship Diagram (ERD)

An ERD is a relationship visual representation of a database. The visualization shows relationships between entities in a database. An Entity is a named object composed of data fields (attributes). Attributes can be data types, primitive data types, Time stamps, UUID

### Integrity constrain

Integrity constraints in a database ensure that our data is consistent and correct, not incorrect or dirty; keeps the data clean in a database. Moreover, integrity constraints enforce a set of rules defined by the database admin. It is ideal for our system such that it will enhance the performance of our database queries, either for
validity or to prevent the insertion of incorrect data.

> Integrity constraints can be nullability, uniqueness, etc.

## Entity Relationship in Data Base

The next table summarizes the modeling of a database.

| Concept                         |    Notation     |
| ------------------------------- | :-------------: |
| Attribute                       |      Oval       |
| Entity                          |    Rectangle    |
| Relationship                    |     Diamond     |
| Is-A Relationship               |    Triangle     |
| Unique                          | Underlined Text |
| Participates 0 or more times    |      Line       |
| Participates 1 or more times    |    Bold Line    |
| Participates at most once       |      Arrow      |
| Participates once and only once |   Bold Arrow    |

## Relationship Types

Many - Many
Many - One
One - One

### Example

User - Wave **(Many to Many)**
A User must have a token.
A Wave must have a client_id.
A Wave must have a wave number.
A Wave must have a start date.
A Wave must have an end date.
A User belongs to 1 or more Waves.
A User belongs at to least 1 Wave.
A Wave must have at least 1 User.

User - Window **(Many to One)**
A User must have a token.
A Window must have a start time.
A Window must have a closing time.
A Window must have a creation time.
A Window must have at most one and a single User. (Possible Change)
A User must have 1 or more Windows.

Window - Tab **(Many to One)**
A Window must have at least one Tab.
A Tab belongs to at most one Window.

Tab - Domain **(Many to One)**
A Tab has at most one Domain.
A Domain belongs to at least one Tab.

Tab - HTML **(Many to Many)**
A Tab has at least one HTML.
An HTML belongs to at least one Tab.

Tab - Click **(Many to One)**
A Tab can have clicks.
A Click belongs to at least and only one Tab.

Tab - Scroll **(Many to One)**
A Tab can have scrolls.
A Scroll belongs to at least one and only Tab.

## ERD Diagram

![ERD GESIS](./images/entity_relationship_diagram.png)
