#!/usr/local/bin/perl
# Create, update or delete a scheduled mail

require './schedule-lib.pl';
&ReadParseMime();
if (!$in{'new'}) {
	$sched = &get_schedule($in{'id'});
	$cron = &find_cron_job($sched);
	}
else {
	$sched = { };
	}

if ($in{'delete'}) {
	# Just remove schedule
	&delete_schedule($sched);
	&cron::delete_cron_job($cron) if ($cron);
	}
else {
	# Validate and store inputs
	&error_setup($text{'save_err'});
	$in{'subject'} || &error($text{'save_esubject'});
	$sched->{'subject'} = $in{'subject'};
	$in{'mail'} =~ s/\r//g;
	if ($in{'mail'} =~ /\S/ && $in{'mail'} !~ /\n$/) {
		$in{'mail'} .= "\n";
		}
	$sched->{'mail'} = $in{'mail'};
	if ($config{'attach'}) {
		if ($in{'mail_def'}) {
			-r $in{'mailfile'} || &error($text{'save_emailfile'});
			$sched->{'mailfile'} = $in{'mailfile'};
			}
		else {
			$sched->{'mailfile'} = undef;
			}
		}
	if ($in{'to_def'}) {
		delete($sched->{'to'});
		}
	else {
		$in{'to'} || &error($text{'save_eto'});
		$sched->{'to'} = $in{'to'};
		}
	if ($mailbox::config{'edit_from'} == 1) {
		if ($in{'from_def'}) {
			delete($sched->{'from'});
			}
		else {
			$in{'from'} || &error($text{'save_efrom'});
			$sched->{'from'} = $in{'from'};
			}
		}
	$sched->{'cc'} = $in{'cc'};
	$sched->{'bcc'} = $in{'bcc'};
	$sched->{'enabled'} = $in{'enabled'};
	if ($in{'mode'} == 1) {
		# At time
		eval { $sched->{'at'} = timelocal(0, $in{'min'}, $in{'hour'},
						  $in{'day'}, $in{'month'}-1, 
						  $in{'year'}-1900) };
		$@ && &error($text{'save_eat'});
		}
	else {
		# Cron time
		delete($sched->{'at'});
		&cron::parse_times_input($sched, \%in);
		}

	# Create or update the schedule
	&save_schedule($sched);
	&cron::delete_cron_job($cron) if ($cron);
	if (!$sched->{'at'}) {
		$job = { "command" => "$cron_cmd $sched->{'id'}",
			 "user" => $remote_user,
			 "active" => 1,
			 "special" => $sched->{'special'},
			 "mins" => $sched->{'mins'},
			 "hours" => $sched->{'hours'},
			 "days" => $sched->{'days'},
			 "months" => $sched->{'months'},
			 "weekdays" => $sched->{'weekdays'} };
		&cron::create_cron_job($job);
		}

	if ($config{'upload'}) {
		# Add an attached file
		if ($in{'upload'}) {
			&create_schedule_file($sched, $in{'upload'}, $in{'upload_filename'} || "unknown");
			}

		# Remove deleted files
		@files = &list_schedule_files($sched);
		foreach $d (split(/\0/, $in{'d'})) {
			($file) = grep { $_->{'id'} eq $d } @files;
			&delete_schedule_file($sched, $file) if ($file);
			}
		}
	}

# If this is a one-off job, make sure a cron job exists to detect them
&create_atmode_job();

&redirect("");

