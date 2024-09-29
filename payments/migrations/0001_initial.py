# Generated by Django 5.0.6 on 2024-09-29 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MpesaCallback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('merchant_request_id', models.CharField(max_length=255)),
                ('checkout_request_id', models.CharField(max_length=255)),
                ('result_code', models.IntegerField()),
                ('result_desc', models.CharField(max_length=255)),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('mpesa_receipt_number', models.CharField(blank=True, max_length=255, null=True)),
                ('transaction_date', models.DateTimeField(blank=True, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_type', models.CharField(max_length=50)),
                ('service_id', models.PositiveIntegerField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_method', models.CharField(choices=[('PAYPAL', 'PayPal'), ('MPESA', 'Mpesa')], max_length=10)),
                ('payment_plan', models.CharField(choices=[('pay_upfront', 'Upfront'), ('2_month_inst', 'Two Months'), ('3_month_ins', 'Three Months')], max_length=15)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('FAILED', 'Failed'), ('SUCCESS', 'Success')], default='PENDING', max_length=10)),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='PreSignup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('phone_number', models.CharField(max_length=15)),
                ('service_type', models.CharField(max_length=50)),
                ('service_id', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]