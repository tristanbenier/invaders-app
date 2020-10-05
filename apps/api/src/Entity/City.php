<?php

namespace App\Entity;

use ApiPlatform\Core\Annotation\ApiResource;
use App\Repository\CityRepository;
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;
use Symfony\Component\Serializer\Annotation\Groups;

/**
 * @ApiResource()
 *
 * @ORM\Table(name="i_city")
 * @ORM\Entity(repositoryClass=CityRepository::class)
 */
class City
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
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $name;

    /**
     * @ORM\Column(type="string", length=100)
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $slug;

    /**
     * @ORM\Column(type="string", length=10)
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $prefix;

    /**
     * @ORM\OneToMany(targetEntity=Invader::class, mappedBy="city", orphanRemoval=true)
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
