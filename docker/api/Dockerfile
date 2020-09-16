FROM php:7.1-apache

ENV SYMFONY_ALLOW_APPDEV=1

COPY default.conf /etc/apache2/sites-available/000-default.conf

RUN a2enmod rewrite

WORKDIR /apps/api

# =========================
# PHP Configuration

# Install GD
RUN apt-get update \
    && apt-get install -y libfreetype6-dev libjpeg62-turbo-dev libpng-dev \
    && docker-php-ext-configure gd --with-freetype-dir=/usr/include/ --with-jpeg-dir=/usr/include/ \
    && docker-php-ext-install gd

# Install MCrypt
RUN apt-get update \
    && apt-get install -y libmcrypt-dev \
    && docker-php-ext-install mcrypt

# Install Intl
RUN apt-get update \
    && apt-get install -y libicu-dev \
    && docker-php-ext-install intl

# Install Mysql
RUN docker-php-ext-install mysqli pdo_mysql

# Install mbstring
RUN docker-php-ext-install mbstring

# Install soap
RUN apt-get update \
    && apt-get install -y libxml2-dev \
    && docker-php-ext-install soap

# Install opcache
RUN docker-php-ext-install opcache

# Install PHP zip extension
RUN docker-php-ext-install zip

# Install Git
RUN apt-get update \
    && apt-get install -y git

# Install xsl
RUN apt-get update \
    && apt-get install -y libxslt-dev \
    && docker-php-ext-install xsl

# Install imagick
RUN apt-get update && apt-get install -y libmagickwand-dev --no-install-recommends
RUN pecl install imagick && docker-php-ext-enable imagick

# Install Nano
RUN apt-get install nano

# Install Composer
RUN curl -sS https://getcomposer.org/installer | php \
    && mv composer.phar /usr/local/bin/composer

# Change PHP limits
RUN touch /usr/local/etc/php/conf.d/upload.ini \
    && echo "post_max_size = 512M;" >> /usr/local/etc/php/conf.d/uploads.ini \
    && echo "upload_max_filesize = 512M;" >> /usr/local/etc/php/conf.d/uploads.ini \
    && echo "memory_limit = 512M;" >> /usr/local/etc/php/conf.d/uploads.ini
