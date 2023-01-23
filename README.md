# enigma-public-access-modules
Plug-able access modules for enigma

##  License
See [LICENSE.md](.github/LICENSE.md)

### Pre-requisistes

- Install Docker
```bash
brew install docker docker-compose
```

- Install Docker Container Runtime
https://github.com/abiosoft/colima
```bash
brew install colima
colima start
```
### Setup

1. Create pytest.ini file from pytest.ini .sample file. Edit the DJANGO_SETTINGS_MODULE to the settings path.

### How to run tests

1. Tests:
If docker is not running, the command will first load up the service and then run the tests.
```bash
make test
```

2. Linter:
Docker should be running for linter tool:
```bash
   docker exec dev make lint
```
