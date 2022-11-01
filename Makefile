DOCK=docker-compose
RUN=$(DOCK) run --rm api
EXEC=$(DOCK) exec api
SF=$(RUN) bin/console
FRONT_NPM=cd apps/front && npm
DB_PORT=3306

install: build api-build front-build
lint: api-lint front-lint
test: api-test front-test

############################### API

api-build: api-vendor-install api-db-create api-db-schema-update
api-config:
	@echo "Configuring API authentication..."
	@echo ""
	- $(RUN) mkdir -p config/jwt
	- $(RUN) openssl genpkey -out config/jwt/private.pem -aes256 -algorithm rsa -pkeyopt rsa_keygen_bits:4096
	- $(RUN) openssl pkey -in config/jwt/private.pem -out config/jwt/public.pem -pubout
api-load-fixtures:
	$(RUN) bin/console doctrine:fixtures:load

# Application control
api-start: api-up db-wait
	@echo " => API available on http://localhost:8000"
	@echo " => PMA available on http://localhost:8889"
api-stop:
	$(DOCK) stop
api-restart: api-stop api-start
api-up:
	$(DOCK) up -d

# Vendors management commands

api-vendor-install:
	$(RUN) composer install

api-vendor-update:
	$(RUN) composer update

api-vendor-clear:
	- rm -rf vendor

api-vendor-require:
	$(RUN) composer require $(lib)

api-vendor-require-dev:
	$(RUN) composer require --dev $(lib)

# Symfony commands

api-db-create:
	$(SF) doctrine:database:create --if-not-exists

api-db-schema-update:
	$(SF) doctrine:schema:update --force

api-make-entity:
	$(SF) make:entity

api-db-make-migration:
	$(SF) make:migration

api-db-migrate:
	$(SF) doctrine:migrations:migrate

api-db-remove:
	$(SF) doctrine:database:drop --force --if-exists

api-db-reset: db-remove db

api-test:
	$(RUN) composer test

api-lint:
	- $(RUN) composer stan
	- $(RUN) composer cscheck

api-cc:
	- $(SF) cache:clear
	- $(SF) liip:imagine:cache:remove

api-clean:
	- rm -rf var/cache/*
	- rm -rf var/logs/*
	- rm -rf var/sessions/*

api-perm:
	- $(EXEC) chmod 777 -R var
	$(EXEC) chmod 777 -R vendor

############################### FRONT

front-build:
	- cd apps/front && npm i

front-start:
	- cd apps/front && npm run dev

front-generate:
	- cd apps/front && npm run generate

front-lint:
	- cd apps/front && npm run lint

front-test:
	- cd apps/front && npm run test

front-deploy:
	- cd apps/front && npm run deploy

# ----------------------------
# Internals
build:
	$(DOCK) build

db-wait:	# Wait for database connection
	$(RUN) php -r "for(;;){if(@fsockopen('db',$(DB_PORT))){break;}}"

remove:
	$(DOCK) rm -vf

ssh:
	$(EXEC) bash
