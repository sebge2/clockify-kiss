# Clockify Kiss

## Description

This tool has been inspired by the project [clockify-cli](https://github.com/t5/clockify-cli).
The purpose of this tool is to specify is time entries in a file. This file contains all the entries of 
a particular period. Time entries contained in this file are then synchronized with Clockify. During
this synchronization, time entries that are still relevant are preserved on Clockify those that are no more,
are deleted, missing time entries are added. 

This tool aims to simplify and make the encoding process faster. This tool considers that most of
the time (during a period), time entries are related to a single task, then some time-to-time there
are exceptions. 


## Installation

Move to the main directory that contains setup.py

```
pip3 install -e .
```

Then create a file ``~/.clockify.cfg``, this file contains:
* your personal token,
* when a working day starts/ends
* the details of a public holiday
* the details of a personal holiday

```` 
{
    "token": "XXXXXXXXXXXX",
    "publicHoliday": {
        "project": "ALL_Absence",
        "task": "Public Holiday",
        "description": "OFF",
        "tags": [
            "@ Home"
        ]
    },
    "personalHoliday": {
        "project": "ALL_Absence",
        "task": "Vacations",
        "description": "OFF",
        "tags": [
            "@ Home"
        ]
    },
    "day":{
        "startAt": "08:00:00",
        "endAt": "16:00:00"
    }
}
````

## Usage

### Fill Time Entries

The tool reads the specified file (see bellow), generates all the time-entries then it compares 
with Clockify, performs some checks. After that, a report is displayed to the end-user. The user
is able to decide if he wants to apply time entries on Clockify, or not.

The time entries generator works like this: 
1. Time-entries are filled with public holidays. 
1. Personal holidays are filled for days that are no public holidays. 
So the interval may contain public holidays.
1. Specific tasks are filled, those tasks cannot overlap public/personal holidays.
1. Then default tasks are used to fill gaps; a gap happens when a working day has not the expected
number of time.

Note that:
* all intervals can be spread over several days. In that case, the interval will be split in to
several intervals, one per day. Don't worry, the command explicitly displays all it will be applied.
* this tool does not support lunch time, it considers that a working day has no interruption

````
{
  "period": {
    "fromDate": "2020-01-01",
    "toDate": "2020-01-31"
  },
  "personalHolidays": [
    {
      "interval": {
        "fromDate": "2020-01-09 08:00:00",
        "toDate": "2020-01-09 16:00:00"
      }
    }
  ],
  "publicHolidays": [
    "2020-01-01"
  ],
  "defaultTasks": [
    {
      "project": "DEV_PRJ_Mobile whitelabel",
      "description": "White label",
      "interval": {
        "fromDate": "2020-01-01",
        "toDate": "2020-01-31"
      },
      "tags": [
        "@ Office"
      ]
    }
  ],
  "tasks": [
    {
      "project": "DEV_ORG_Sprint Meetings",
      "description": "POC",
      "interval": {
        "fromDate": "2020-01-06 09:00:00",
        "toDate": "2020-01-06 12:00:00"
      },
      "tags": [
        "@ Office"
      ]
    },
    {
      "project": "DEV_ORG_Sprint Meetings",
      "description": "POC",
      "interval": {
        "fromDate": "2020-01-07 08:00:00",
        "toDate": "2020-01-07 10:00:00"
      },
      "tags": [
        "@ Office"
      ]
    },
    {
      "project": "ALL_Company events",
      "description": "Annual Event",
      "interval": {
        "fromDate": "2020-01-17 12:00:00",
        "toDate": "2020-01-17 16:00:00"
      },
      "tags": [
        "@ Other"
      ]
    },
    {
      "project": "DEV_ORG_Sprint Meetings",
      "description": "Review",
      "interval": {
        "fromDate": "2020-01-24 14:00:00",
        "toDate": "2020-01-24 16:00:00"
      },
      "tags": [
        "@ Office"
      ]
    }
  ]
}
````

The output of ``clockifyKiss fill-time-entries ~/Documents/clockify-2020-01.json`` will be:
````

_________ .__                 __   .__  _____             ____  __.__
\_   ___ \|  |   ____   ____ |  | _|__|/ ____\__.__.     |    |/ _|__| ______ ______
/    \  \/|  |  /  _ \_/ ___\|  |/ /  \   __<   |  |     |      < |  |/  ___//  ___/
\     \___|  |_(  <_> )  \___|    <|  ||  |  \___  |     |    |  \|  |\___ \ \___ \
 \______  /____/\____/ \___  >__|_ \__||__|  / ____|     |____|__ \__/____  >____  >
        \/                 \/     \/         \/                  \/       \/     \/

======================================================================================
======================================================================================


Wednesday 2020-01-01
	[KEEP]	ALL_Absence - Public Holiday "OFF" ['@ Home']: [2020-01-01, 08:00:00 => 2020-01-01, 16:00:00] 

	Duration in hour(s): 8.0


Thursday 2020-01-02
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-02, 08:00:00 => 2020-01-02, 16:00:00] 

	Duration in hour(s): 8.0


Friday 2020-01-03
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-03, 08:00:00 => 2020-01-03, 16:00:00] 

	Duration in hour(s): 8.0


Saturday 2020-01-04

	Duration in hour(s): 0.0


Sunday 2020-01-05

	Duration in hour(s): 0.0


============
= NEW WEEK =
============


Monday 2020-01-06
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-06, 08:00:00 => 2020-01-06, 09:00:00] 
	[KEEP]	DEV_ORG_Sprint Meetings - None "POC" ['@ Office']: [2020-01-06, 09:00:00 => 2020-01-06, 12:00:00] 
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-06, 12:00:00 => 2020-01-06, 16:00:00] 

	Duration in hour(s): 8.0


Tuesday 2020-01-07
	[KEEP]	DEV_ORG_Sprint Meetings - None "POC" ['@ Office']: [2020-01-07, 08:00:00 => 2020-01-07, 10:00:00] 
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-07, 10:00:00 => 2020-01-07, 16:00:00] 

	Duration in hour(s): 8.0


Wednesday 2020-01-08
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-08, 08:00:00 => 2020-01-08, 16:00:00] 

	Duration in hour(s): 8.0


Thursday 2020-01-09
	[KEEP]	ALL_Absence - Vacations "OFF" ['@ Home']: [2020-01-09, 08:00:00 => 2020-01-09, 16:00:00] 

	Duration in hour(s): 8.0


Friday 2020-01-10
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-10, 08:00:00 => 2020-01-10, 16:00:00] 

	Duration in hour(s): 8.0


Saturday 2020-01-11

	Duration in hour(s): 0.0


Sunday 2020-01-12

	Duration in hour(s): 0.0


============
= NEW WEEK =
============


Monday 2020-01-13
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-13, 08:00:00 => 2020-01-13, 16:00:00] 

	Duration in hour(s): 8.0


Tuesday 2020-01-14
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-14, 08:00:00 => 2020-01-14, 16:00:00] 

	Duration in hour(s): 8.0


Wednesday 2020-01-15
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-15, 08:00:00 => 2020-01-15, 16:00:00] 

	Duration in hour(s): 8.0


Thursday 2020-01-16
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-16, 08:00:00 => 2020-01-16, 16:00:00] 

	Duration in hour(s): 8.0


Friday 2020-01-17
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-17, 08:00:00 => 2020-01-17, 12:00:00] 
	[KEEP]	ALL_Company events - None "Annual Event" ['@ Other']: [2020-01-17, 12:00:00 => 2020-01-17, 16:00:00] 

	Duration in hour(s): 8.0


Saturday 2020-01-18

	Duration in hour(s): 0.0


Sunday 2020-01-19

	Duration in hour(s): 0.0


============
= NEW WEEK =
============


Monday 2020-01-20
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-20, 08:00:00 => 2020-01-20, 16:00:00] 

	Duration in hour(s): 8.0


Tuesday 2020-01-21
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-21, 08:00:00 => 2020-01-21, 16:00:00] 

	Duration in hour(s): 8.0


Wednesday 2020-01-22
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-22, 08:00:00 => 2020-01-22, 16:00:00] 

	Duration in hour(s): 8.0


Thursday 2020-01-23
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-23, 08:00:00 => 2020-01-23, 16:00:00] 

	Duration in hour(s): 8.0


Friday 2020-01-24
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-24, 08:00:00 => 2020-01-24, 14:00:00] 
	[KEEP]	DEV_ORG_Sprint Meetings - None "Review" ['@ Office']: [2020-01-24, 14:00:00 => 2020-01-24, 16:00:00] 

	Duration in hour(s): 8.0


Saturday 2020-01-25

	Duration in hour(s): 0.0


Sunday 2020-01-26

	Duration in hour(s): 0.0


============
= NEW WEEK =
============


Monday 2020-01-27
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-27, 08:00:00 => 2020-01-27, 16:00:00] 

	Duration in hour(s): 8.0


Tuesday 2020-01-28
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-28, 08:00:00 => 2020-01-28, 16:00:00] 

	Duration in hour(s): 8.0


Wednesday 2020-01-29
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-29, 08:00:00 => 2020-01-29, 16:00:00] 

	Duration in hour(s): 8.0


Thursday 2020-01-30
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-30, 08:00:00 => 2020-01-30, 16:00:00] 

	Duration in hour(s): 8.0


Friday 2020-01-31
	[KEEP]	DEV_PRJ_Mobile whitelabel - None "White label" ['@ Office']: [2020-01-31, 08:00:00 => 2020-01-31, 16:00:00] 

	Duration in hour(s): 8.0




===========
= SUMMARY =
===========

Up-to-date with Clockify: YES
Duration issue(s): NO
Number public holidays in day(s): 1.0
Number personal holidays in hour(s): 1.0

Do you want to apply those time entries? [y/N]: 
````


### Others

Other commands are also available, please refer to:

````
clockifyKiss --help
````

You can list projects, tasks of a project, fetch your time-entries, ...
