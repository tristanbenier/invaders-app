<?php

namespace App\Controller\Image;

use App\Entity\Image;
use App\Exception\BadRequestJsonException;
use App\Exception\NotFoundJsonException;
use App\Repository\InvaderRepository;
use Symfony\Component\HttpFoundation\Request;

final class CreateImageAction
{
    public function __construct(InvaderRepository $invaderRepository)
    {
        $this->invaderRepository = $invaderRepository;
    }

    public function __invoke(Request $request): Image
    {
        $uploadedFile = $request->files->get('file');
        if (!$uploadedFile) {
            throw new BadRequestJsonException('"file" is required');
        }

        $invaderId = $request->request->get('invaderId');
        $invader = $this->invaderRepository->find((int) $invaderId);
        if (!$invader) {
            throw new NotFoundJsonException(sprintf('Invader %d not found', $invaderId));
        }

        $image = new Image();
        $image->setFile($uploadedFile);
        $image->setInvader($invader);

        return $image;
    }
}
