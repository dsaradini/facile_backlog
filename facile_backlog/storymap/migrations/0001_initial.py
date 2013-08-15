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
            ('title', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
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
            ('phase', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storymap.Phase'])),
            ('theme', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storymap.Theme'])),
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
        u'storymap.phase': {
            'Meta': {'object_name': 'Phase'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'story_map': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'phases'", 'to': u"orm['storymap.StoryMap']"})
        },
        u'storymap.story': {
            'Meta': {'object_name': 'Story'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phase': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['storymap.Phase']"}),
            'theme': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['storymap.Theme']"}),
            'title': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        u'storymap.storymap': {
            'Meta': {'object_name': 'StoryMap'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'storymap.theme': {
            'Meta': {'object_name': 'Theme'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'story_map': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'themes'", 'to': u"orm['storymap.StoryMap']"})
        }
    }

    complete_apps = ['storymap']