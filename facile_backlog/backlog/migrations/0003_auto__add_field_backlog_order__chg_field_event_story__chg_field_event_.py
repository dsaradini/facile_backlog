# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Backlog.order'
        db.add_column(u'backlog_backlog', 'order',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)


        # Changing field 'Event.story'
        db.alter_column(u'backlog_event', 'story_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['backlog.UserStory']))

        # Changing field 'Event.backlog'
        db.alter_column(u'backlog_event', 'backlog_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['backlog.Backlog']))

    def backwards(self, orm):
        # Deleting field 'Backlog.order'
        db.delete_column(u'backlog_backlog', 'order')


        # Changing field 'Event.story'
        db.alter_column(u'backlog_event', 'story_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['backlog.UserStory']))

        # Changing field 'Event.backlog'
        db.alter_column(u'backlog_event', 'backlog_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['backlog.Backlog']))

    models = {
        u'backlog.authorizationassociation': {
            'Meta': {'object_name': 'AuthorizationAssociation'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['backlog.Project']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.User']"})
        },
        u'backlog.backlog': {
            'Meta': {'ordering': "('kind', 'last_modified')", 'object_name': 'Backlog'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'default': "'03:general'", 'max_length': '16'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'backlogs'", 'null': 'True', 'to': u"orm['backlog.Project']"})
        },
        u'backlog.event': {
            'Meta': {'ordering': "('-when',)", 'object_name': 'Event'},
            'backlog': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'events'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['backlog.Backlog']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'to': u"orm['backlog.Project']"}),
            'story': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'events'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['backlog.UserStory']"}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'to': u"orm['core.User']"}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'backlog.project': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Project'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'story_counter': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects'", 'symmetrical': 'False', 'through': u"orm['backlog.AuthorizationAssociation']", 'to': u"orm['core.User']"})
        },
        u'backlog.userstory': {
            'Meta': {'object_name': 'UserStory'},
            'acceptances': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'as_a': ('django.db.models.fields.TextField', [], {}),
            'backlog': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stories'", 'to': u"orm['backlog.Backlog']"}),
            'color': ('django.db.models.fields.CharField', [], {'max_length': '7', 'blank': 'True'}),
            'comments': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'i_want_to': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'points': ('django.db.models.fields.FloatField', [], {'default': '-1.0'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stories'", 'to': u"orm['backlog.Project']"}),
            'so_i_can': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'to_do'", 'max_length': '20'}),
            'theme': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
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
        }
    }

    complete_apps = ['backlog']