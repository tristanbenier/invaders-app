<?php

namespace App\Entity;

use ApiPlatform\Core\Annotation\ApiProperty;
use App\Repository\ImageRepository;
use Doctrine\ORM\Mapping as ORM;
use Symfony\Component\HttpFoundation\File\File;
use Symfony\Component\Serializer\Annotation\Groups;
use Vich\UploaderBundle\Mapping\Annotation as Vich;

/**
 * @ORM\Entity(repositoryClass=ImageRepository::class)
 *
 * @Vich\Uploadable
 */
class Image
{
    /**
     * @ORM\Id
     * @ORM\GeneratedValue
     * @ORM\Column(type="integer")
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $id;

    /**
     * @ORM\Column(type="string", length=100)
     */
    private $filename;

    /**
     * @var File|null
     *
     * @Vich\UploadableField(mapping="image", fileNameProperty="filename")
     */
    private $file;

    /**
     * @var string|null
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $fileUrl;

    /**
     * @ORM\ManyToOne(targetEntity=Invader::class, inversedBy="images")
     * @ORM\JoinColumn(nullable=false)
     */
    private $invader;

    public function getId(): ?int
    {
        return $this->id;
    }

    public function getFilename(): ?string
    {
        return $this->filename;
    }

    public function setFilename(string $filename): self
    {
        $this->filename = $filename;

        return $this;
    }

    public function getFile(): ?File
    {
        return $this->file;
    }

    public function setFile(File $file): self
    {
        $this->file = $file;

        return $this;
    }

    /**
     * @ApiProperty(iri="http://schema.org/fileUrl")
     */
    public function getFileUrl(): ?string
    {
        return $this->fileUrl;
    }

    public function getThumbnailFileUrl(): ?string
    {
        $fileUrl = $this->fileUrl;
        if ($fileUrl) {
            $parts = explode('.', $fileUrl);
            $extension = array_pop($parts);
            return join('.', $parts) . '_thumb.' . $extension;
        }
        return $fileUrl;
    }

    public function setFileUrl(string $fileUrl): self
    {
        $this->fileUrl = $fileUrl;

        return $this;
    }

    public function getInvader(): ?Invader
    {
        return $this->invader;
    }

    public function setInvader(?Invader $invader): self
    {
        $this->invader = $invader;

        return $this;
    }
}
