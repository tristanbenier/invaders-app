<?php

namespace App\EventSubscriber;

use ApiPlatform\Core\EventListener\EventPriorities;
use ApiPlatform\Core\Util\RequestAttributesExtractor;
use App\Entity\Image;
use App\Entity\Invader;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Event\ViewEvent;
use Symfony\Component\HttpKernel\KernelEvents;
use Vich\UploaderBundle\Storage\StorageInterface;

final class ResolveImageFileUrlSubscriber implements EventSubscriberInterface
{
    /** @var StorageInterface */
    private $storage;

    public function __construct(
        StorageInterface $storage
    ) {
        $this->storage = $storage;
    }

    public static function getSubscribedEvents(): array
    {
        return [
            KernelEvents::VIEW => ['onPreSerialize', EventPriorities::PRE_SERIALIZE],
        ];
    }

    public function onPreSerialize(ViewEvent $event): void
    {
        $controllerResult = $event->getControllerResult();
        $request = $event->getRequest();

        if ($controllerResult instanceof Response || !$request->attributes->getBoolean('_api_respond', true)) {
            return;
        }

        $attributes = RequestAttributesExtractor::extractAttributes($request);
        if (!$attributes || !is_a($attributes['resource_class'], Invader::class, true)) {
            return;
        }

        $invaders = $controllerResult;

        if (!is_iterable($invaders)) {
            $invaders = [$invaders];
        }

        foreach ($invaders as $invader) {
            if (!$invader instanceof Invader) {
                continue;
            }
            $this->setInvaderImagesUrl($invader);
        }
    }

    private function setInvaderImagesUrl(Invader $invader): void
    {
        $images = $invader->getImages();

        foreach ($images as $image) {
            $this->setImageUrl($image);
        }
    }

    private function setImageUrl(Image $image): void
    {
        $imageUrl = $this->storage->resolveUri($image, 'file');

        $image->setFileUrl($imageUrl);
    }
}
