<?php

namespace App\Repository;

use App\Entity\Invader;
use Doctrine\Bundle\DoctrineBundle\Repository\ServiceEntityRepository;
use Doctrine\Persistence\ManagerRegistry;

/**
 * @method Invader|null find($id, $lockMode = null, $lockVersion = null)
 * @method Invader|null findOneBy(array $criteria, array $orderBy = null)
 * @method Invader[]    findAll()
 * @method Invader[]    findBy(array $criteria, array $orderBy = null, $limit = null, $offset = null)
 */
class InvaderRepository extends ServiceEntityRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, Invader::class);
    }

    // /**
    //  * @return Invader[] Returns an array of Invader objects
    //  */
    /*
    public function findByExampleField($value)
    {
        return $this->createQueryBuilder('i')
            ->andWhere('i.exampleField = :val')
            ->setParameter('val', $value)
            ->orderBy('i.id', 'ASC')
            ->setMaxResults(10)
            ->getQuery()
            ->getResult()
        ;
    }
    */

    /*
    public function findOneBySomeField($value): ?Invader
    {
        return $this->createQueryBuilder('i')
            ->andWhere('i.exampleField = :val')
            ->setParameter('val', $value)
            ->getQuery()
            ->getOneOrNullResult()
        ;
    }
    */
}
