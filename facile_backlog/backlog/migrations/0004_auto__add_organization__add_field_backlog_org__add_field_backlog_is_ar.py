# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Organization'
        db.create_table(u'backlog_organization', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('web_site', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
        ))
        db.send_create_signal(u'backlog', ['Organization'])

        # Adding field 'Backlog.org'
        db.add_column(u'backlog_backlog', 'org',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='backlogs', null=True, to=orm['backlog.Organization']),
                      keep_default=False)

        # Adding field 'Backlog.is_archive'
        db.add_column(u'backlog_backlog', 'is_archive',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Backlog.auto_status'
        db.add_column(u'backlog_backlog', 'auto_status',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=20, blank=True),
                      keep_default=False)

        # Adding field 'Backlog.is_main'
        db.add_column(u'backlog_backlog', 'is_main',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Project.org'
        db.add_column(u'backlog_project', 'org',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='projects', null=True, to=orm['backlog.Organization']),
                      keep_default=False)

        # Adding field 'Project.last_modified'
        db.add_column(u'backlog_project', 'last_modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now=True, blank=True),
                      keep_default=False)

        # Adding field 'Event.organization'
        db.add_column(u'backlog_event', 'organization',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='events', null=True, on_delete=models.SET_NULL, to=orm['backlog.Organization']),
                      keep_default=False)


        # Changing field 'Event.when'
        db.alter_column(u'backlog_event', 'when', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Event.project'
        db.alter_column(u'backlog_event', 'project_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['backlog.Project']))
        # Adding field 'AuthorizationAssociation.org'
        db.add_column(u'backlog_authorizationassociation', 'org',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='authorizations', null=True, to=orm['backlog.Organization']),
                      keep_default=False)


        # Changing field 'AuthorizationAssociation.project'
        db.alter_column(u'backlog_authorizationassociation', 'project_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['backlog.Project']))
        # Adding unique constraint on 'AuthorizationAssociation', fields ['project', 'user']
        db.create_unique(u'backlog_authorizationassociation', ['project_id', 'user_id'])

        # Adding unique constraint on 'AuthorizationAssociation', fields ['org', 'user']
        db.create_unique(u'backlog_authorizationassociation', ['org_id', 'user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'AuthorizationAssociation', fields ['org', 'user']
        db.delete_unique(u'backlog_authorizationassociation', ['org_id', 'user_id'])

        # Removing unique constraint on 'AuthorizationAssociation', fields ['project', 'user']
        db.delete_unique(u'backlog_authorizationassociation', ['project_id', 'user_id'])

        # Deleting model 'Organization'
        db.delete_table(u'backlog_organization')

        # Deleting field 'Backlog.org'
        db.delete_column(u'backlog_backlog', 'org_id')

        # Deleting field 'Backlog.is_archive'
        db.delete_column(u'backlog_backlog', 'is_archive')

        # Deleting field 'Backlog.auto_status'
        db.delete_column(u'backlog_backlog', 'auto_status')

        # Deleting field 'Backlog.is_main'
        db.delete_column(u'backlog_backlog', 'is_main')

        # Deleting field 'Project.org'
        db.delete_column(u'backlog_project', 'org_id')

        # Deleting field 'Project.last_modified'
        db.delete_column(u'backlog_project', 'last_modified')

        # Deleting field 'Event.organization'
        db.delete_column(u'backlog_event', 'organization_id')


        # Changing field 'Event.when'
        db.alter_column(u'backlog_event', 'when', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))

        # Changing field 'Event.project'
        db.alter_column(u'backlog_event', 'project_id', self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['backlog.Project']))
        # Deleting field 'AuthorizationAssociation.org'
        db.delete_column(u'backlog_authorizationassociation', 'org_id')


        # Changing field 'AuthorizationAssociation.project'
        db.alter_column(u'backlog_authorizationassociation', 'project_id', self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['backlog.Project']))

    models = {
        u'backlog.authorizationassociation': {
            'Meta': {'unique_together': "(('user', 'project'), ('user', 'org'))", 'object_name': 'AuthorizationAssociation'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
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
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'backlogs'", 'null': 'True', 'to': u"orm['backlog.Project']"})
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
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'org': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'projects'", 'null': 'True', 'to': u"orm['backlog.Organization']"}),
            'story_counter': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects'", 'symmetrical': 'False', 'through': u"orm['backlog.AuthorizationAssociation']", 'to': u"orm['core.User']"})
        },
        u'backlog.userstory': {
            'Meta': {'object_name': 'UserStory'},
            'acceptances': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'as_a': ('django.db.models.fields.TextField', [], {}),
            'backlog': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stories'", 'to': u"orm['backlog.Backlog']"}),
            'color': ('django.db.models.fields.CharField', [], {'max_length': '7', 'blank': 'True'}),
            'comments': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
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