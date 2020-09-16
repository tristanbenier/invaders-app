# Happics repo

## Installation

### Requirements

- docker (https://docs.docker.com/get-docker/)
- nodejs (https://nodejs.org/en/download/)
- stripe CLI (https://stripe.com/docs/stripe-cli)

### Installation

#### Process

```bash
# Configure the applications ports as you wish
cp .env.dist .env
# Launch installation
make install
```

#### Install wkhtmltox library

```bash
# Launch API
make api-start
# SSH in API container
make ssh
# Install library
cd /tmp
curl -O -L -C - https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.jessie_amd64.deb
dpkg -i wkhtmltox_0.12.5-1.jessie_amd64.deb
apt-get install -f
dpkg -i wkhtmltox_0.12.5-1.jessie_amd64.deb
# Test library is installed
wkhtmltopdf --version
```

#### Configuration

Configure global ENV variables for applications
```bash
# Copy .env file for front app
cp apps/front/.env.dist apps/front/.env
# Copy .env file for admin app
cp apps/admin/.env.dist apps/admin/.env
# Override .env files for API app
touch apps/api/.env.local # To override values from apps/api/.env file
touch apps/api/.env.dev.local # To override values from apps/api/.env.dev file
touch apps/api/.env.test.local # To override values from apps/api/.env.test file
```

#### Credentials

When installation is complete, one user has been created for admin app, and another for front app.
One applications are launched (see below), you will be able to access to:

- Login in front application on [http://localhost:8001](http://localhost:8001) (credentials: `user@petitcube.com` | `password`)
- Access to admin application on [http://localhost:8002](http://localhost:8002) (credentials: `admin@petitcube.com` | `password`)

## Usage

### Launch application

```bash
# Launch API (on a specific tab)
make api-start
# Launch Front application (on a specific tab)
make front-start
# Launch Admin application (on a specific tab)
make admin-start
```

### Stripe webhooks

You need to launch Stripe listener in order to perform credit purchases locally.

```bash
# Login
stripe login
# Run webhook listener
stripe listen --events payment_intent.succeeded --forward-to localhost:8000/payment/stripe/payment_intents/succeeded
```

### Tests

You can launch the tests with:

```bash
make test
```

### Lint and code analysis

You can launch the linters (and code analyzer) with:

```bash
make lint
# make api-lint
# make front-lint
# make admin-lint
```

---

## Notes

Docker architecture inspired from:

-  https://github.com/eko/docker-symfony (commit 6bdd6db - 1 Dec 2019)

- https://knplabs.com/fr/blog/how-to-dockerise-a-symfony-4-project
