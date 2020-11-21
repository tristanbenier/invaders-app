<?php

namespace App\Entity;

use ApiPlatform\Core\Annotation\ApiProperty;
use ApiPlatform\Core\Annotation\ApiResource;
use App\Repository\CityRepository;
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;
use Symfony\Component\HttpFoundation\File\File;
use Symfony\Component\Serializer\Annotation\Groups;
use Vich\UploaderBundle\Mapping\Annotation as Vich;

/**
 * @ApiResource(
 *     iri="http://schema.org/Image",
 *     normalizationContext={"groups"={"city:read"}},
 *     collectionOperations={
 *         "get"={"normalization_context"={"groups"="city:collection:read"}},
 *         "post"
 *     },
 *     itemOperations={"get", "put", "delete"}
 * )
 *
 * @ORM\Table(name="i_city")
 * @ORM\Entity(repositoryClass=CityRepository::class)
 *
 * @Vich\Uploadable
 */
class City
{
    /**
     * @ORM\Id
     * @ORM\GeneratedValue
     * @ORM\Column(type="integer")
     *
     * @Groups({"city:read", "city:collection:read", "invader:read", "invader:collection:read"})
     */
    private $id;

    /**
     * @ORM\Column(type="string", length=100)
     *
     * @Groups({"city:read", "city:collection:read", "invader:read", "invader:collection:read"})
     */
    private $name;

    /**
     * @ORM\Column(type="string", length=100)
     *
     * @Groups({"city:read", "city:collection:read", "invader:read", "invader:collection:read"})
     */
    private $slug;

    /**
     * @ORM\Column(type="string", length=10)
     *
     * @Groups({"city:read", "city:collection:read", "invader:read", "invader:collection:read"})
     */
    private $prefix;

    /**
     * @ORM\Column(type="string", length=100)
     */
    private $filename;

    /**
     * @var File|null
     *
     * @Vich\UploadableField(mapping="city_image", fileNameProperty="filename")
     */
    private $file;

    /**
     * @var string|null
     *
     * @Groups({"city:read", "city:collection:read"})
     */
    private $fileUrl;

    /**
     * @var string|null
     *
     * @Groups({"city:read", "city:collection:read"})
     */
    private $thumbnailUrl;

    /**
     * @ORM\OneToMany(targetEntity=Invader::class, mappedBy="city", orphanRemoval=true)
     *
     * @Groups({"city:read"})
     */
    private $invaders;

    public function __construct()
    {
        $this->invaders = new ArrayCollection();
    }

    public function getId(): ?int
    {
        return $this->id;
    }

    public function getName(): ?string
    {
        return $this->name;
    }

    public function setName(string $name): self
    {
        $this->name = $name;

        return $this;
    }

    public function getSlug(): ?string
    {
        return $this->slug;
    }

    public function setSlug(string $slug): self
    {
        $this->slug = $slug;

        return $this;
    }

    public function getPrefix(): ?string
    {
        return $this->prefix;
    }

    public function setPrefix(string $prefix): self
    {
        $this->prefix = $prefix;

        return $this;
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

    /**
     * @return Collection|Invader[]
     */
    public function getInvaders(): Collection
    {
        return $this->invaders;
    }

    public function addInvader(Invader $invader): self
    {
        if (!$this->invaders->contains($invader)) {
            $this->invaders[] = $invader;
            $invader->setCity($this);
        }

        return $this;
    }

    public function removeInvader(Invader $invader): self
    {
        if ($this->invaders->contains($invader)) {
            $this->invaders->removeElement($invader);
            // set the owning side to null (unless already changed)
            if ($invader->getCity() === $this) {
                $invader->setCity(null);
            }
        }

        return $this;
    }
}
