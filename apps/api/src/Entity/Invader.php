<?php

namespace App\Entity;

use ApiPlatform\Core\Annotation\ApiResource;
use App\Repository\InvaderRepository;
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;
use Symfony\Component\Serializer\Annotation\Groups;

/**
 * @ApiResource(
 *     normalizationContext={"groups"={"invader:read"}},
 *     collectionOperations={
 *         "get"={"normalization_context"={"groups"="invader:collection:read"}},
 *         "post"
 *     },
 *     itemOperations={"get", "put", "delete"}
 * )
 *
 * @ORM\Entity(repositoryClass=InvaderRepository::class)
 * @ORM\Table(indexes={@ORM\Index(name="invader_name_idx", columns={"name"})})
 */
class Invader
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
     * @ORM\Column(type="string", length=30, nullable=true)
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $name;

    /**
     * @ORM\Column(type="smallint", nullable=true)
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $points;

    /**
     * @ORM\Column(type="string", length=255)
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $address1;

    /**
     * @ORM\Column(type="string", length=255, nullable=true)
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $address2;

    /**
     * @ORM\Column(type="string", length=10, nullable=true)
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $zipcode;

    /**
     * @ORM\ManyToOne(targetEntity=City::class, inversedBy="invaders")
     * @ORM\JoinColumn(nullable=false)
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $city;

    /**
     * @ORM\Column(type="string", length=255, nullable=true)
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $comment;

    /**
     * @ORM\Column(type="float")
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $latitude;

    /**
     * @ORM\Column(type="float")
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $longitude;

    /**
     * @ORM\ManyToOne(targetEntity=Status::class, inversedBy="invaders")
     * @ORM\JoinColumn(nullable=false)
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $status;

    /**
     * @ORM\ManyToMany(targetEntity=User::class, mappedBy="invaders")
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $users;

    /**
     * @ORM\OneToMany(targetEntity=Image::class, mappedBy="invader", orphanRemoval=true)
     *
     * @Groups({"invader:read", "invader:collection:read"})
     */
    private $images;

    public function __construct()
    {
        $this->users = new ArrayCollection();
        $this->images = new ArrayCollection();
    }

    public function getId(): ?int
    {
        return $this->id;
    }

    public function getName(): ?string
    {
        return $this->name;
    }

    public function setName(?string $name): self
    {
        $this->name = $name;

        return $this;
    }

    public function getPoints(): ?int
    {
        return $this->points;
    }

    public function setPoints(?int $points): self
    {
        $this->points = $points;

        return $this;
    }

    public function getAddress1(): ?string
    {
        return $this->address1;
    }

    public function setAddress1(string $address1): self
    {
        $this->address1 = $address1;

        return $this;
    }

    public function getAddress2(): ?string
    {
        return $this->address2;
    }

    public function setAddress2(?string $address2): self
    {
        $this->address2 = $address2;

        return $this;
    }

    public function getZipcode(): ?string
    {
        return $this->zipcode;
    }

    public function setZipcode(?string $zipcode): self
    {
        $this->zipcode = $zipcode;

        return $this;
    }

    public function getCity(): ?City
    {
        return $this->city;
    }

    public function setCity(?City $city): self
    {
        $this->city = $city;

        return $this;
    }

    public function getComment(): ?string
    {
        return $this->comment;
    }

    public function setComment(?string $comment): self
    {
        $this->comment = $comment;

        return $this;
    }

    public function getLatitude(): ?float
    {
        return $this->latitude;
    }

    public function setLatitude(float $latitude): self
    {
        $this->latitude = $latitude;

        return $this;
    }

    public function getLongitude(): ?float
    {
        return $this->longitude;
    }

    public function setLongitude(float $longitude): self
    {
        $this->longitude = $longitude;

        return $this;
    }

    public function getStatus(): ?Status
    {
        return $this->status;
    }

    public function setStatus(?Status $status): self
    {
        $this->status = $status;

        return $this;
    }

    /**
     * @return Collection|User[]
     */
    public function getUsers(): Collection
    {
        return $this->users;
    }

    public function addUser(User $user): self
    {
        if (!$this->users->contains($user)) {
            $this->users[] = $user;
            $user->addInvader($this);
        }

        return $this;
    }

    public function removeUser(User $user): self
    {
        if ($this->users->contains($user)) {
            $this->users->removeElement($user);
            $user->removeInvader($this);
        }

        return $this;
    }

    /**
     * @return Collection|Image[]
     */
    public function getImages(): Collection
    {
        return $this->images;
    }

    public function addImage(Image $image): self
    {
        if (!$this->images->contains($image)) {
            $this->images[] = $image;
            $image->setInvader($this);
        }

        return $this;
    }

    public function removeImage(Image $image): self
    {
        if ($this->images->contains($image)) {
            $this->images->removeElement($image);
            // set the owning side to null (unless already changed)
            if ($image->getInvader() === $this) {
                $image->setInvader(null);
            }
        }

        return $this;
    }
}
