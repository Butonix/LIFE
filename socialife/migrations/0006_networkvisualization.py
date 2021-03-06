# Generated by Django 2.2.4 on 2019-12-17 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('socialife', '0005_post_bookmarked_by'),
    ]

    operations = [
        migrations.CreateModel(
            name='NetworkVisualization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('degree_centrality', models.ImageField(default='/network_visualization/Eigenvector_Centrality.png', upload_to='network_visualization')),
                ('betweenness_centrality', models.ImageField(default='/network_visualization/Eigenvector_Centrality.png', upload_to='network_visualization')),
                ('closeness_centrality', models.ImageField(default='/network_visualization/Eigenvector_Centrality.png', upload_to='network_visualization')),
                ('eigenvector_centrality', models.ImageField(default='/network_visualization/Eigenvector_Centrality.png', upload_to='network_visualization')),
                ('clustering_coefficient', models.ImageField(default='/network_visualization/Eigenvector_Centrality.png', upload_to='network_visualization')),
                ('visualization', models.ImageField(default='/network_visualization/Eigenvector_Centrality.png', upload_to='network_visualization')),
                ('da', models.TextField()),
                ('ba', models.TextField()),
                ('ca', models.TextField()),
                ('ea', models.TextField()),
                ('cca', models.TextField()),
            ],
        ),
    ]
