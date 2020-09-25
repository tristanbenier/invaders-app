<?php

namespace App\Exception;

use Symfony\Component\HttpFoundation\Response;
use Throwable;

class NotFoundJsonException extends JsonException
{
    public function __construct(string $message = null, Throwable $previous = null, int $code = 0, array $headers = [])
    {
        parent::__construct(Response::HTTP_NOT_FOUND, $message, $previous, $headers, $code);
    }
}
