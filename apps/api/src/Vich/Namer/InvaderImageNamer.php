<?php

namespace App\Vich\Namer;

use Symfony\Component\HttpFoundation\File\UploadedFile;
use Vich\UploaderBundle\Mapping\PropertyMapping;
use Vich\UploaderBundle\Naming\ConfigurableInterface;
use Vich\UploaderBundle\Naming\NamerInterface;
use Vich\UploaderBundle\Util\Transliterator;

class InvaderImageNamer implements NamerInterface, ConfigurableInterface
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
        $invader = $object->getInvader();
        $invaderName = $invader->getName();

        if ($invaderName) {
            return sprintf('%s_%s.jpg', $invaderName, uniqid());
        }

        return uniqid() . '.jpg';
    }
}
