# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Project.lang'
        db.add_column(u'backlog_project', 'lang',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=3, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Project.lang'
        db.delete_column(u'backlog_project', 'lang')


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
        u'backlog.backlog': {
            'Meta': {'ordering': "('order',)", 'object_name': 'Backlog'},
            'auto_status': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_archive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_main': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'kind': ('django.db.models.fields.CharField', [], {'default': "'general'", 'max_length': '16'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'org': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'backlogs'", 'null': 'True', 'to': u"orm['backlog.Organization']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'backlogs'", 'null': 'True', 'to': u"orm['backlog.Project']"})
        },
        u'backlog.event': {
            'Meta': {'ordering': "('-when',)", 'object_name': 'Event'},
            'backlog': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'events'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['backlog.Backlog']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'events'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['backlog.Organization']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['backlog.Project']"}),
            'story': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'events'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['backlog.UserStory']"}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'to': u"orm['core.User']"}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
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
            'lang': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'org': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'projects'", 'null': 'True', 'to': u"orm['backlog.Organization']"}),
            'story_counter': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects'", 'symmetrical': 'False', 'through': u"orm['backlog.AuthorizationAssociation']", 'to': u"orm['core.User']"})
        },
        u'backlog.statistic': {
            'Meta': {'ordering': "('day',)", 'object_name': 'Statistic'},
            'data': ('json_field.fields.JSONField', [], {'default': "u'null'"}),
            'day': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'statistics'", 'to': u"orm['backlog.Project']"})
        },
        u'backlog.userstory': {
            'Meta': {'object_name': 'UserStory'},
            'acceptances': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'as_a': ('django.db.models.fields.TextField', [], {}),
            'backlog': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stories'", 'to': u"orm['backlog.Backlog']"}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'color': ('django.db.models.fields.CharField', [], {'max_length': '7', 'blank': 'True'}),
            'comments': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'i_want_to': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'points': ('django.db.models.fields.FloatField', [], {'default': '-1.0'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stories'", 'to': u"orm['backlog.Project']"}),
            'so_i_can': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
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