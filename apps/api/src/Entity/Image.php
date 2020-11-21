<?php

namespace App\Entity;

use ApiPlatform\Core\Annotation\ApiProperty;
use ApiPlatform\Core\Annotation\ApiResource;
use App\Repository\ImageRepository;
use App\Controller\Image\CreateImageAction;
use App\Controller\Image\RemoveImageAction;
use Doctrine\ORM\Mapping as ORM;
use Symfony\Component\HttpFoundation\File\File;
use Symfony\Component\Serializer\Annotation\Groups;
use Vich\UploaderBundle\Mapping\Annotation as Vich;

/**
 * @ApiResource(
 *     iri="http://schema.org/Image",
 *     normalizationContext={"groups"={"image:read"}},
 *     collectionOperations={
 *         "get",
 *         "post"={
 *             "controller"=CreateImageAction::class,
 *             "deserialize"=false,
 *             "validation_groups"={"Default", "image:create"},
 *             "openapi_context"={
 *                 "requestBody"={
 *                     "content"={
 *                         "multipart/form-data"={
 *                             "schema"={
 *                                 "type"="object",
 *                                 "properties"={
 *                                     "file"={
 *                                         "type"="string",
 *                                         "format"="binary"
 *                                     }
 *                                 }
 *                             }
 *                         }
 *                     }
 *                 }
 *             }
 *         }
 *     },
 *     itemOperations={
 *         "get",
 *         "delete": {
 *         }
 *     }
 * )
 *
 * @ORM\Table(name="i_image")
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
     * @Groups({"image:read", "invader:read", "invader:collection:read"})
     */
    private $id;

    /**
     * @ORM\Column(type="string", length=100)
     */
    private $filename;

    /**
     * @var File|null
     *
     * @Vich\UploadableField(mapping="invader_image", fileNameProperty="filename")
     */
    private $file;

    /**
     * @var string|null
     *
     * @Groups({"image:read", "invader:read", "invader:collection:read"})
     */
    private $fileUrl;

    /**
     * @var string|null
     *
     * @Groups({"image:read", "invader:read", "invader:collection:read"})
     */
    private $thumbnailUrl;

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

    public function setFilename(?string $filename): self
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

    public function setFileUrl(string $fileUrl): self
    {
        $this->fileUrl = $fileUrl;

        return $this;
    }
    public function getThumbnailUrl(): ?string
    {
        return $this->thumbnailUrl;
    }

    public function setThumbnailUrl(string $thumbnailUrl): self
    {
        $this->thumbnailUrl = $thumbnailUrl;

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
