<?php

namespace App\Controller\Image;

use App\Exception\NotFoundJsonException;
use App\Repository\ImageRepository;
use Doctrine\ORM\EntityManagerInterface;
use Vich\UploaderBundle\Storage\StorageInterface;

final class RemoveImageAction
{
    /** @var StorageInterface */
    private $storage;

    public function __construct(
        StorageInterface $storage
    ) {
        $this->storage = $storage;
    }

    public function __invoke(
        int $id,
        ImageRepository $imageRepository,
        EntityManagerInterface $entityManager
    ): void {
        $image = $imageRepository->find($id);

        if (!$image) {
            throw new NotFoundJsonException(sprintf('Image %s not found', $id));
        }

        $filePath = $this->storage->resolvePath($image, 'file');
        @unlink($filePath);

        $entityManager->remove($image);
        $entityManager->flush();
    }
}
