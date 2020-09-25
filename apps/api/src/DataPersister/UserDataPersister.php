<?php

namespace App\DataPersister;

use ApiPlatform\Core\DataPersister\DataPersisterInterface;
use App\Entity\User;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Component\Security\Core\Encoder\UserPasswordEncoderInterface;

class UserDataPersister implements DataPersisterInterface
{
    /** @var EntityManagerInterface */
    private $entityManager;

    /** @var UserPasswordEncoderInterface */
    private $encoder;

    public function __construct(
        EntityManagerInterface $entityManager,
        UserPasswordEncoderInterface $userPasswordEncoder
    ) {
        $this->entityManager = $entityManager;
        $this->encoder = $userPasswordEncoder;
    }

    /**
     * @param mixed $data
     */
    public function supports($data): bool
    {
        return $data instanceof User;
    }

    /**
     * @param User $data
     */
    public function persist($data): void
    {
        $user = $data;
        if ($user->getPlainPassword()) {
            $user->setPassword(
                $this->encoder->encodePassword($user, $user->getPlainPassword())
            );
            $user->eraseCredentials();
        }

        $this->entityManager->persist($user);
        $this->entityManager->flush();
    }

    /**
     * @param User $data
     */
    public function remove($data): void
    {
        $this->entityManager->remove($data);
        $this->entityManager->flush();
    }
}
