<?php

namespace App\Vich\Namer;

use Vich\UploaderBundle\Mapping\PropertyMapping;
use Vich\UploaderBundle\Naming\ConfigurableInterface;
use Vich\UploaderBundle\Naming\NamerInterface;
use Vich\UploaderBundle\Util\Transliterator;

class CityNamer implements NamerInterface, ConfigurableInterface
{
    /** @var bool */
    private $transliterate = false;

    /**
     * @param array $options Options for this namer. The following options are accepted:
     *                       - transliterate: whether the filename should be transliterated or not
     */
    public function configure(array $options): void
    {
        $this->transliterate = isset($options['transliterate']) ? (bool) $options['transliterate'] : $this->transliterate;
    }

    /**
     * {@inheritdoc}
     */
    public function name($object, PropertyMapping $mapping): string
    {
        $city = $object->getCity();
        $invaderSlug = $city->getSlug();

        if ($invaderSlug) {
            return sprintf('%s_%s.jpg', $invaderSlug, uniqid());
        }

        return uniqid() . '.jpg';
    }
}
