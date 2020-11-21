<?php

namespace App\EventSubscriber;

use ApiPlatform\Core\EventListener\EventPriorities;
use ApiPlatform\Core\Util\RequestAttributesExtractor;
use App\Entity\City;
use App\Entity\Image;
use App\Entity\Invader;
use Liip\ImagineBundle\Imagine\Cache\CacheManager;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Event\ViewEvent;
use Symfony\Component\HttpKernel\KernelEvents;
use Vich\UploaderBundle\Storage\StorageInterface;

final class ResolveImageFileUrlSubscriber implements EventSubscriberInterface
{
    /** @var StorageInterface */
    private $vichStorage;

    /** @var CacheManager */
    private $imagineCache;

    public function __construct(
        StorageInterface $vichStorage,
        CacheManager $imagineCache
    ) {
        $this->vichStorage = $vichStorage;
        $this->imagineCache = $imagineCache;
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
        if (!$attributes) {
            return;
        }

        $resources = $controllerResult;
        if (!is_iterable($resources)) {
            $resources = [$resources];
        }

        if (is_a($attributes['resource_class'], Invader::class, true)) {
            $this->resolveInvaderImagesUrls($resources);
        }

        if (is_a($attributes['resource_class'], Image::class, true)) {
            $this->resolveImagesUrls($resources);
        }

        if (is_a($attributes['resource_class'], City::class, true)) {
            $this->resolveCityImagesUrls($resources);
        }
    }

    private function resolveCityImagesUrls(iterable $cities): void
    {
        foreach ($cities as $city) {
            if (!$city instanceof City) {
                continue;
            }

            $imageUrl = $this->vichStorage->resolveUri($city, 'file');
            $thumbnailUrl = $this->imagineCache->getBrowserPath($imageUrl, 'city_thumbnail');

            if ($imageUrl) {
                $city->setFileUrl($imageUrl);
            }
            if ($thumbnailUrl) {
                $city->setThumbnailUrl($thumbnailUrl);
            }
        }
    }

    private function resolveInvaderImagesUrls(iterable $invaders): void
    {
        foreach ($invaders as $invader) {
            if (!$invader instanceof Invader) {
                continue;
            }
            $this->setInvaderImagesUrl($invader);
        }
    }

    private function resolveImagesUrls(iterable $images): void
    {
        foreach ($images as $image) {
            if (!$image instanceof Image) {
                continue;
            }
            $this->setImageUrls($image);
        }
    }

    private function setInvaderImagesUrl(Invader $invader): void
    {
        $images = $invader->getImages();

        foreach ($images as $image) {
            $this->setImageUrls($image);
        }
    }

    private function setImageUrls(Image $image): void
    {
        $imageUrl = $this->vichStorage->resolveUri($image, 'file');
        $thumbnailUrl = $this->imagineCache->getBrowserPath($imageUrl, 'invader_thumbnail');

        $image->setFileUrl($imageUrl);
        $image->setThumbnailUrl($thumbnailUrl);
    }
}
