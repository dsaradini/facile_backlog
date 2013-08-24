# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Story.color'
        db.add_column(u'storymap_story', 'color',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=7, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Story.color'
        db.delete_column(u'storymap_story', 'color')


    models = {
        u'storymap.phase': {
            'Meta': {'ordering': "('order',)", 'object_name': 'Phase'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'story_map': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'phases'", 'to': u"orm['storymap.StoryMap']"})
        },
        u'storymap.story': {
            'Meta': {'ordering': "('order',)", 'object_name': 'Story'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '7', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'phase': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stories'", 'to': u"orm['storymap.Phase']"}),
            'theme': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stories'", 'to': u"orm['storymap.Theme']"}),
            'title': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        u'storymap.storymap': {
            'Meta': {'object_name': 'StoryMap'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'})
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