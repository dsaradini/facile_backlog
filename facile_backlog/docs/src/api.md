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
<code type="block">
{
	'username': 'USERNAME',
	'password': 'PASSWORD'
}
</code>

Response
--------
<code type="block">
{
	'token': 'MY_API_TOKEN',
}
</code>

`/api/projects/`
================
**List all projects the logged-in user is member of**

Allow: *GET*, *HEAD*, *OPTIONS*

Response
--------
<code type="block">
[
	...list of project json element...
	...see /api/project/[project-id]/
]
</code>

`/api/project/[project-id]/`
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
	"backlogs": [
		{
			"id": BACKLOG_ID,
			"url": "https://app.backlogman.com/api/projects/PROJECT_ID/backlogs/BACKLOG_ID/",
			"name": "BACKLOG_NAME",
			"description": "BACKLOG_DESCRIPTION",
			"story_count": 0
		},
		...list...
	]
}
</code>

`/api/project/[project-id]/backlogs/`
====================================
**All backlogs in a project**

Allow: *GET*, *HEAD*, *OPTIONS*

Response
--------
<code type="block">
[
	...list of backlog json element...
	...see /api/project/[project-id]/backlogs/[backlog-id]
]
</code>

`/api/project/[project-id]/backlogs/[backlog-id]`
==================================================
**Detail on a given project**

Allow: *GET*, *HEAD*, *OPTIONS*

Response
--------
<code type="block">
{
	"id": BACKLOG_ID,
	"url": "https://app.backlogman.com/api/projects/P_ID/backlogs/B_ID/",
	"name": "BACKLOG_NAME",
	"description": "BACKLOG_DESCRIPTION",
	"story_count": 0
}
</code>

`/api/project/[project-id]/backlogs/[backlog-id]/stories/`
==========================================================
**All *ordered* stories in a backlog**

Allow: *GET*, *HEAD*, *OPTIONS*

Response
--------
<code type="block">
[
	...list of stories json element...
	...see `/api/project/[project-id]/backlogs/[backlog-id]/stories/[story-id]/`
]
</code>

`/api/project/[project-id]/backlogs/[backlog-id]/stories/[story-id]/`
====================================================================
**Details on a given story**

Allow: *GET*, *HEAD*, *OPTIONS*

Response
--------
<code type="block">
{
	"id": STORY_ID,
	"code": "PCODE-XXX",
	"url": "https://app.backlogman.com/api/projects/P_ID/backlogs/B_ID/stories/S_ID/",
	"as_a": "an api user",
	"i_want_to": "be able to read project info using REST API",
	"so_i_can": "create a client on mobile device",
	"color": "#0033FF",
	"comments": "",
	"acceptances": "- Can query project\n- Can query backlog\n- Can query story"
	"points": STORY_POINTS,
	"create_date": "2013-06-19T15:04:08.254Z",
	"theme": "Story theme in project",
	"status": "to_do|in_progress|accepted|rejected"
}
</code>