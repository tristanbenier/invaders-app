<?php

namespace App\Entity;

use ApiPlatform\Core\Annotation\ApiResource;
use App\Repository\StatusRepository;
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;
use Symfony\Component\Serializer\Annotation\Groups;

/**
 * @ApiResource()
 *
 * @ORM\Table(name="i_status")
 * @ORM\Entity(repositoryClass=StatusRepository::class)
 */
class Status
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
     * @ORM\Column(type="string", length=30)
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $name;

    /**
     * @ORM\Column(type="string", length=30)
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $color;

    /**
     * @ORM\OneToMany(targetEntity=Invader::class, mappedBy="status", orphanRemoval=true)
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

    public function getColor(): ?string
    {
        return $this->color;
    }

    public function setColor(string $color): self
    {
        $this->color = $color;

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
            $invader->setStatus($this);
        }

        return $this;
    }

    public function removeInvader(Invader $invader): self
    {
        if ($this->invaders->contains($invader)) {
            $this->invaders->removeElement($invader);
            // set the owning side to null (unless already changed)
            if ($invader->getStatus() === $this) {
                $invader->setStatus(null);
            }
        }

        return $this;
    }
}
