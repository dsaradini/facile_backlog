# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StoryMap'
        db.create_table(u'storymap_storymap', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.OneToOneField')(related_name='story_map', unique=True, null=True, to=orm['backlog.Project'])),
        ))
        db.send_create_signal(u'storymap', ['StoryMap'])

        # Adding model 'Theme'
        db.create_table(u'storymap_theme', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('story_map', self.gf('django.db.models.fields.related.ForeignKey')(related_name='themes', to=orm['storymap.StoryMap'])),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal(u'storymap', ['Theme'])

        # Adding model 'Phase'
        db.create_table(u'storymap_phase', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('story_map', self.gf('django.db.models.fields.related.ForeignKey')(related_name='phases', to=orm['storymap.StoryMap'])),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal(u'storymap', ['Phase'])

        # Adding model 'Story'
        db.create_table(u'storymap_story', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('phase', self.gf('django.db.models.fields.related.ForeignKey')(related_name='stories', to=orm['storymap.Phase'])),
            ('theme', self.gf('django.db.models.fields.related.ForeignKey')(related_name='stories', to=orm['storymap.Theme'])),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('color', self.gf('django.db.models.fields.CharField')(default='#ffc', max_length=7, blank=True)),
        ))
        db.send_create_signal(u'storymap', ['Story'])


    def backwards(self, orm):
        # Deleting model 'StoryMap'
        db.delete_table(u'storymap_storymap')

        # Deleting model 'Theme'
        db.delete_table(u'storymap_theme')

        # Deleting model 'Phase'
        db.delete_table(u'storymap_phase')

        # Deleting model 'Story'
        db.delete_table(u'storymap_story')


    models = {
        u'backlog.authorizationassociation': {
            'Meta': {'unique_together': "(('user', 'project'), ('user', 'org'))", 'object_name': 'AuthorizationAssociation'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'org': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'authorizations'", 'null': 'True', 'to': u"orm['backlog.Organization']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'authorizations'", 'null': 'True', 'to': u"orm['backlog.Project']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.User']"})
        },
        u'backlog.organization': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Organization'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organizations'", 'symmetrical': 'False', 'through': u"orm['backlog.AuthorizationAssociation']", 'to': u"orm['core.User']"}),
            'web_site': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
        },
        u'backlog.project': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Project'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'org': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'projects'", 'null': 'True', 'to': u"orm['backlog.Organization']"}),
            'story_counter': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects'", 'symmetrical': 'False', 'through': u"orm['backlog.AuthorizationAssociation']", 'to': u"orm['core.User']"})
        },
        u'core.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '1023', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'storymap.phase': {
            'Meta': {'ordering': "('order',)", 'object_name': 'Phase'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'story_map': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'phases'", 'to': u"orm['storymap.StoryMap']"})
        },
        u'storymap.story': {
            'Meta': {'ordering': "('order',)", 'object_name': 'Story'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'#ffc'", 'max_length': '7', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'phase': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stories'", 'to': u"orm['storymap.Phase']"}),
            'theme': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stories'", 'to': u"orm['storymap.Theme']"}),
            'title': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        u'storymap.storymap': {
            'Meta': {'object_name': 'StoryMap'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'story_map'", 'unique': 'True', 'null': 'True', 'to': u"orm['backlog.Project']"})
        },
        u'storymap.theme': {
            'Meta': {'ordering': "('order',)", 'object_name': 'Theme'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'story_map': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'themes'", 'to': u"orm['storymap.StoryMap']"})
        }
    }

    complete_apps = ['storymap']