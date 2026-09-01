variable "region" {
  description = "Регион AWS"
  type        = string
  default     = "eu-central-1"
}

variable "bucket_name" {
  description = "Имя S3-бакета для файлов (должно быть глобально уникальным)"
  type        = string
}

variable "instance_type" {
  description = "Тип инстанса. t3.micro входит во free tier"
  type        = string
  default     = "t3.micro"
}

variable "image" {
  description = "Docker-образ приложения, опубликованный CI"
  type        = string
  default     = "ghcr.io/senpai520120/django_application:latest"
}

variable "ssh_cidr" {
  description = "С какого адреса пускать SSH. Пусто — порт закрыт совсем"
  type        = string
  default     = ""
}

variable "key_name" {
  description = "Имя SSH-ключа в AWS. Пусто — без ключа"
  type        = string
  default     = ""
}
