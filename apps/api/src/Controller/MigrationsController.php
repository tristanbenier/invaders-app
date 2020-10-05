<?php

namespace App\Controller;

use App\Entity\City;
use App\Entity\Image;
use App\Entity\Invader;
use App\Entity\Status;
use App\Exception\NotFoundJsonException;
use App\Repository\CityRepository;
use App\Repository\ImageRepository;
use App\Repository\InvaderRepository;
use App\Repository\StatusRepository;
use App\Repository\UserRepository;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\Routing\Annotation\Route;

class MigrationsController extends AbstractController
{
    private const MIGRATED_STATUS = 'migrated';
    private const EXISTING_STATUS = 'existing';
    private const SKIPPED_STATUS = 'skipped';
    private const FAILED_STATUS = 'failed';

    /** @var InvaderRepository */
    private $invaderRepository;

    /** @var ImageRepository */
    private $imageRepository;

    /** @var CityRepository */
    private $cityRepository;

    /** @var StatusRepository */
    private $statusRepository;

    /** @var UserRepository */
    private $userRepository;

    /** @var EntityManagerInterface */
    private $entityManager;

    public function __construct(
        InvaderRepository $invaderRepository,
        ImageRepository $imageRepository,
        CityRepository $cityRepository,
        StatusRepository $statusRepository,
        UserRepository $userRepository,
        EntityManagerInterface $entityManager
    ) {
        $this->invaderRepository = $invaderRepository;
        $this->imageRepository = $imageRepository;
        $this->cityRepository = $cityRepository;
        $this->statusRepository = $statusRepository;
        $this->userRepository = $userRepository;
        $this->entityManager = $entityManager;
    }

    /**
     * @Route("/migrations", name="migrations")
     */
    public function migrate(): JsonResponse
    {
        $filepath = $this->getParameter('kernel.project_dir') . '/var/data-invaders.json';
        $invaders = $this->extractInvadersFromFile($filepath);

        $result = [];
        $result[self::MIGRATED_STATUS] = 0;
        $result[self::EXISTING_STATUS] = 0;
        $result[self::SKIPPED_STATUS] = 0;
        $result[self::FAILED_STATUS] = 0;
        $max = 200;
        $count = 0;

        foreach ($invaders as $invaderData) {
            $resultCode = $this->migrateInvader($invaderData);
            $result[$resultCode]++;

            if ($resultCode === self::MIGRATED_STATUS) {
                $count++;
                if ($count === $max) {
                    break;
                }
            }
        }

        return $this->json([
            'success' => $result[self::FAILED_STATUS] === 0,
            'result' => $result,
        ]);
    }

    private function migrateInvader(array $invaderData): string
    {
        $invader = null;

        // Check if invaders already exists
        $invaderName = $invaderData['name'] ?? null;
        if (!$invaderName) {
            return self::SKIPPED_STATUS;
        }
        $invader = $this->invaderRepository->findOneBy(['name' => $invaderName]);
        if ($invader) {
            return self::EXISTING_STATUS;
        }

        $invader = new Invader();
        $invader->setName($invaderName);

        // Migrate status
        $statusData = $invaderData['status'] ?? [];
        $statusName = $statusData['name'] ?? 'Active';
        $status = $this->statusRepository->findOneBy(['name' => $statusName]);
        if (!$status) {
            $status = $this->createStatus($statusName, $statusData['color'] ?? '#ccc');
            return self::SKIPPED_STATUS;
        }
        $invader->setStatus($status);

        // Migrate coordinates
        $coordinates = $invaderData['coordinates'] ?? [];
        $latitude = $coordinates['lat'] ?? null;
        $longitude = $coordinates['lng'] ?? null;
        if (!$latitude || !$longitude) {
            throw new NotFoundJsonException(sprintf('Coordinates not found for invader %s', $invaderName));
        }
        $invader->setLatitude($latitude);
        $invader->setLongitude($longitude);

        // Migrate points
        $points = $invaderData['points'] ?? null;
        if ($points) {
            $invader->setPoints((int) $points);
        }

        // Migrate address
        $addressData = $invaderData['address'] ?? [];
        $invader->setAddress1($addressData['address1']);
        $invader->setAddress2($addressData['address2']);
        $invader->setZipcode($addressData['zipcode']);

        // Migrate city
        $cityData = $addressData['city'] ?? [];
        $cityName = $cityData['name'] ?? null;
        if (!$cityName) {
            return self::SKIPPED_STATUS;
        }
        $city = $this->cityRepository->findOneBy(['name' => $cityName]);
        if (!$city) {
            $city = $this->createCity($cityName, $cityData['slug'] ?? '', $cityData['prefix'] ?? '');
            return self::SKIPPED_STATUS;
        }
        $invader->setcity($city);

        // Migrate comment
        $comment = $invaderData['comment'] ?? null;
        if ($comment) {
            $invader->setComment($comment);
        }

        // Migrate users
        $usersData = $invaderData['users'] ?? [];
        foreach ($usersData as $userData)  {
            $user = $this->userRepository->findOneBy(['name' => $userData['name'] ?? '']);
            if (!$user) {
                continue;
            }
            $invader->addUser($user);
        }

        // Migrate images
        $imagesData = $invaderData['images'] ?? [];
        $storedImagesDirectoryPath = $this->getParameter('kernel.project_dir') . '/var/images';
        $destinationDirectoryPath = $this->getParameter('kernel.project_dir') . '/public/upload/images/invaders';
        foreach ($imagesData as $imageData) {

            $sourcePath = $storedImagesDirectoryPath . '/' . $imageData['filename'];
            $destinationPath = $destinationDirectoryPath . '/' . $imageData['filename'];
            if (file_exists($sourcePath)) {
                $image = new Image();
                $invader->addImage($image);
                $image->setFilename($imageData['filename']);
                copy($sourcePath, $destinationPath);

                $this->entityManager->persist($image);
            }
        }

        $this->entityManager->persist($invader);
        $this->entityManager->flush();

        return self::MIGRATED_STATUS;
    }

    private function createStatus(string $name, string $color): Status
    {
        $status = new Status();
        $status->setName($name);
        $status->setColor($color);

        $this->entityManager->persist($status);
        $this->entityManager->flush();

        return $status;
    }

    private function createCity(string $name, string $slug, string $prefix): City
    {
        $city = new City();
        $city->setName($name);
        $city->setSlug($slug);
        $city->setPrefix($prefix);

        $this->entityManager->persist($city);
        $this->entityManager->flush();

        return $city;
    }

    private function extractInvadersFromFile(string $filepath): array
    {
        $invaders = [];

        if (file_exists($filepath)) {
            $data = file_get_contents($filepath);

            if ($data) {
                $invaders = json_decode($data, true);
            }
        }

        return $invaders;
    }
}
