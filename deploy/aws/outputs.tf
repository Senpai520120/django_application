output "app_url" {
  description = "Адрес приложения"
  value       = "http://${aws_instance.app.public_ip}/"
}

output "bucket" {
  description = "Бакет с файлами"
  value       = aws_s3_bucket.files.bucket
}

output "instance_id" {
  description = "Инстанс приложения"
  value       = aws_instance.app.id
}
