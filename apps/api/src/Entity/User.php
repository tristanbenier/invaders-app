<?php

namespace App\Entity;

use ApiPlatform\Core\Annotation\ApiResource;
use App\Repository\UserRepository;
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;
use Symfony\Bridge\Doctrine\Validator\Constraints\UniqueEntity;
use Symfony\Component\Security\Core\User\UserInterface;
use Symfony\Component\Serializer\Annotation\Groups;
use Symfony\Component\Serializer\Annotation\SerializedName;

/**
 * @ApiResource()
 *
 * @ORM\Table(name="i_user")
 * @ORM\Entity(repositoryClass=UserRepository::class)
 *
 * @UniqueEntity(fields={"email"})
 */
class User implements UserInterface
{
    public const ROLE_USER = 'ROLE_USER';

    /**
     * @ORM\Id()
     * @ORM\GeneratedValue()
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
     * @ORM\Column(type="string", length=180, unique=true)
     */
    private $email;

    /**
     * @ORM\Column(type="string", length=100)
     */
    private $stringifiedRoles = '';

    /**
     * @ORM\Column(type="string")
     */
    private $password;

    /**
     * @SerializedName("password")
     */
    private $plainPassword;

    /**
     * @ORM\Column(name="reset_password_token", type="string", unique=false, nullable=true)
     */
    private $resetPasswordToken;

    /**
     * @ORM\ManyToMany(targetEntity=Invader::class, inversedBy="users")
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

    /**
     * A visual identifier that represents this user.
     */
    public function getUsername(): string
    {
        return (string) $this->email;
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

    public function getEmail(): ?string
    {
        return $this->email;
    }

    public function setEmail(string $email): self
    {
        $this->email = $email;

        return $this;
    }

    public function getStringifiedRoles(): string
    {
        return $this->stringifiedRoles;
    }

    public function getRoles(): array
    {
        $roles = explode(',', $this->stringifiedRoles);
        // guarantee every user at least has ROLE_CLIENT
        $roles[] = self::ROLE_USER;

        return array_unique($roles);
    }

    public function setRoles(array $stringifiedRoles): self
    {
        $this->stringifiedRoles = $stringifiedRoles;

        return $this;
    }

    public function getPassword(): string
    {
        return (string) $this->password;
    }

    public function setPassword(string $password): self
    {
        $this->password = $password;

        return $this;
    }

    public function getPlainPassword(): ?string
    {
        return $this->plainPassword;
    }

    public function setPlainPassword(string $plainPassword): self
    {
        $this->plainPassword = $plainPassword;

        return $this;
    }

    public function getSalt(): ?string
    {
        // not needed when using the "bcrypt" algorithm in security.yaml
        return null;
    }

    public function eraseCredentials(): void
    {
        // If you store any temporary, sensitive data on the user, clear it here
        $this->plainPassword = null;
    }

    public function getResetPasswordToken(): string
    {
        return (string) $this->resetPasswordToken;
    }

    public function setResetPasswordToken(?string $resetPasswordToken): self
    {
        $this->resetPasswordToken = $resetPasswordToken;

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
        }

        return $this;
    }

    public function removeInvader(Invader $invader): self
    {
        if ($this->invaders->contains($invader)) {
            $this->invaders->removeElement($invader);
        }

        return $this;
    }
}
