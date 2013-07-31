Backlogman REST API
===================

**All API calls, excepted `/api/api-token-auth/` must be authenticated using the following HTTP header**

Header
------

<code type="block">
	Authorization: Token MY_API_TOKEN
</code>

----

`/api/api-token-auth/`
======================
**Get the API token for a given username / password.**

Allow: *POST*

Request
-------

Type: application/json

+ **'username'** *(string)*
		username of the requested token
+ **'password'** *(string)*
		user password

Response
--------
<code type="block">
{
	'token': 'MY_API_TOKEN',
}
</code>


`/api/organizations/`
================
**List all organizations the logged-in user is member of**

Allow: *GET*, *HEAD*, *OPTIONS*

Response
--------
<code type="block">
[
	...list of organization json element...
	{
        "id": ORG_ID,
        "url": "http://localhost:8000/api/organizations/ORG_ID/",
        "name": "ORG NAME",
        "email": "organization email",
        "web_site": "organization web site"
    },
]
</code>


`/api/organizations/[org-id]/`
============================
**Details for a given organization**

Allow: *GET*, *HEAD*, *OPTIONS*

Response
--------
<code type="block">
{
	"id": ORG_ID,
	"url": "https://app.backlogman.com/api/organizations/ORG_ID/",
	"name": "organization name",
	"email": "organization email",
	"web_site": "organization website URL"
	"description": "organization description",
	"users": [
		{
			"full_name": "John Doe",
			"email": "jdoe@backlogman.com"
		},
		... list ...
	],
	"projects": [
		{
			"id": "project id",
			"name": "project name",
			"url": "https://app.backlogman.com/api/projects/PROJ_ID/",
		},
		... lis t...
	],
	"backlogs": [
		{
			"id": BACKLOG_ID,
			"name": "backlog name",
			"is_main": boolean, is main backlog
			"url": "https://app.backlogman.com/api/backlogs/BACKLOG_ID/",
		},
		... list ...
	]
}
</code>


`/api/projects/`
================
**List all projects the logged-in user is member of**

Will list any project, even projects that are part of an organization

Allow: *GET*, *HEAD*, *OPTIONS*

Response
--------
<code type="block">
[
	{
		"id": PROJECT_ID,
		"url": "https://app.backlogman.com/api/projects/PROJECT_ID/",
		"name": "PROJECT NAME",
		"code": "PCODE",
		"description": "PROJECT_DESCRIPTION",
		"organization_id": ORG_ID ( if any )
	},
	...list...
]
</code>

`/api/projects/[project-id]/`
============================
**Details for a given project**

Allow: *GET*, *HEAD*, *OPTIONS*

Response
--------
<code type="block">
{
	"id": PROJECT_ID,
	"url": "https://app.backlogman.com/api/projects/PROJECT_ID/",
	"name": "PROJECT NAME",
	"code": "PCODE",
	"description": "PROJECT_DESCRIPTION",
	"users": [
		{
			"full_name": "John Doe",
			"email": "jdoe@backlogman.com"
		}
	],
	"story_count": 10,
	"available_themes": [
		"theme one",
		"theme two",
		...list...
	],
	"stats": {
		"estimated_points": (int) "number of estimated remaining points",
        "completed_points": (int) "number of completed points",
        "percent_estimated": (float) "percent of story estimated",
        "percent_completed": (float) "percent of story completed,
        "total_stories": (int) "total number of stories",
        "total_points": (int) "total number of point"
        "completed_stories": (int)"number of completed stories",
        "estimated_stories": (int)"number of estimated stories"
	},
	"backlogs": [
		{
			"id": BACKLOG_ID,
			"name": "backlog name",
			"is_main": boolean, is main backlog
			"url": "https://app.backlogman.com/api/backlogs/BACKLOG_ID/",
		},
		... list ...
	]
}
</code>


`/api/backlogs/[backlog-id]`
==================================================
**Detail on a given backlog**

Backlog is hold by a project or an organization, if project_id is null, org_id is available and vise-versa.

Allow: *GET*, *HEAD*, *OPTIONS*

Response
--------
<code type="block">
{
	"id": BACKLOG_ID,
	"url": "https://app.backlogman.com/api/projects/P_ID/backlogs/B_ID/",
	"name": "BACKLOG_NAME",
	"description": "BACKLOG_DESCRIPTION",
	"organization_id": (if any) ORG_ID,
    "project_id": (if any) PROJECT_ID,
	"available_themes": [
		"theme one",
		"theme two",
		...list...
	],
	"stats": {
		"estimated_points": (int) "number of estimated remaining points",
        "completed_points": (int) "number of completed points",
        "percent_estimated": (float) "percent of story estimated",
        "percent_completed": (float) "percent of story completed,
        "total_stories": (int) "total number of stories",
        "total_points": (int) "total number of point"
        "completed_stories": (int)"number of completed stories",
        "estimated_stories": (int)"number of estimated stories"
	}
}
</code>

`/api/backlogs/[backlog-id]/stories/`
==========================================================
**All *ordered* stories in a backlog**

Allow: *GET*, *POST*, *HEAD*, *OPTIONS*

Response
--------
<code type="block">
[
	...list of stories json element...
	...see `/api/backlogs/[backlog-id]/stories/[story-id]/`
]
</code>

`/api/projects/[project-id]/backlogs/[backlog-id]/stories/[story-id]/`
====================================================================
**Details on a given story**

Allow: *GET*, *PUT*, *PATCH*, *DELETE*, *HEAD*, *OPTIONS*

Response
--------
<code type="block">
{
	"id": STORY_ID,
	"code": "PCODE-XXX",
	"url": "https://app.backlogman.com/backlogs/BACKLOG_ID/stories/STORY_ID/",
	"as_a": "an api user",
	"i_want_to": "be able to read project info using REST API",
	"so_i_can": "create a client on mobile device",
	"color": "#0033FF",
	"comments": "",
	"acceptances": "- Can query project\n- Can query backlog\n- Can query story"
	"points": STORY_POINTS,
	"theme": "Story theme in project",
	"status": "to_do|in_progress|accepted|rejected",
	"backlog_id": BACKLOG_ID
	"project_id": PROJECT_ID
}
</code>

`/api/_move_story/`
====================================================================
Move story in the same backlog or another backlog. This json RPC action can be used
to reorder or move + reorder a backlog.

Target backlog can be a project or organization backlog. To perform such operation, the user must have admin access to both backlog (project or organization authorization) if not,
a 404 is returned.

Allow: *POST*, *OPTIONS*

Request
-------

Type: application/json

+ **'target_backlog'** *(number|string)*
		ID of the backlog to apply the ordering or the target backlog for a move
		special value **project_main_backlog** to move the story directly in its project main backlog useful for rejected stories at the end of iteration
+ **'moved_story'** *(number)*
		ID of the moved story
+ **'order'** *(array of number)*
		(optional) Ordered IDs of target_backlog story, included the moved story in case of a move. If this value
		is omitted, the story will be moved at the end of the target_backlog

<code type="block">
{
	"target_backlog": 123,
	"moved_story": 567,
	"order": [10, 50 , 66, 567, 23, 53]
}
</code>

Response
--------
<code type="block">
{
	"ok": true
}
</code>

`/api/projects/[project-id]/_order_backlog/`
====================================================================
Reorder backlog in a project

Allow: *POST*, *OPTIONS*

Request
-------

Type: application/json

+ **'moved_backlog'** *(number)*
		ID of the moved backlog
+ **'order'** *(array of number)*
		Ordered IDs of project backlog ids

<code type="block">
{
	"moved_backlog": 12,
	"order": [2, 5 , 1]
}
</code>

Response
--------
<code type="block">
{
	"ok": true
}
</code>


`/api/organizations/[org-id]/_order_backlog/`
==========================================
Reorder backlog in an organization

Allow: *POST*, *OPTIONS*

Request
-------

Type: application/json

+ **'moved_backlog'** *(number)*
		ID of the moved backlog
+ **'order'** *(array of number)*
		Ordered IDs of organization backlog ids

<code type="block">
{
	"moved_backlog": 12,
	"order": [2, 5 , 1]
}
</code>

Response
--------
<code type="block">
{
	"ok": true
}
</code>



`/api/stories/[story-id]/status/`
==========================================
Reorder backlog in an organization

Allow: *POST*, *GET*

Request
-------

Type: application/json

+ **'status'** *(string)*
		Status for the story.
	+ 'todo'
	+ 'in_progress'
	+ 'completed'
	+ 'accepted'
	+ 'rejected'

<code type="block">
{
	"status": 'completed,
}
</code>

Response
--------

<code type="block">
GET
{
	"status": 'completed'
}
</code>


<code type="block">
POST
{
	"ok": true
}
</code>

Backlogman WebSocker API
========================

2 web sockets are available to be notified of change on organization and project

<code type="block">
	wss://app.backlogman.com/ws/projects/(project-id)
	wss://app.backlogman.com/ws/organizations/(org-id)
</code>

When connected to the specific WebSocket, you will receive all notifications for any elements contained in the project or organization (stories, backlogs)

## Messages

Messages are json utf-8 encoded string

### Move story

type: **stories_moved**

Notification received when a story is moved in or out a backlog

<code type="block">
{
	'backlog_id': (backlog-id), // Backlog id where the story is moved
    'type': "stories_moved",
    'order': [1,6 ,89, 34, 54], // Ordered of <story-id> in the backlog
    'moved_story_id': (story-id), // id of the story moved
    'username': (user-email), // email of the user who made the change
}
</code>

### Story changed

type: **story_changed**

Notification received when a story content has changed ***Only 'status' for the moment***

<code type="block">
{
	'type': "story_changed",
    'story_id': (story-id), // id of the story changed
    'story_data': {...}, json data of the story (see GET story)
    'username': (user-email), // email of the user who made the change
}
</code>

### Backlog moved

type: **backlogs_moved**

Notification received when the backlog order has changed in an organization or project

<code type="block">
{
	'type': "backlogs_moved",
    'order': [1,6 ,89, 34, 54], // Ordered of <backlog-id> in the project or organization
    'username': (user-email), // email of the user who made the change
}
</code>


[Back to index](index)