<?php

require_once('fitbitphp.php');
require_once('config.php');

$fitbit = new FitBitPHP(CLIENT_KEY, CLIENT_SECRET);
$fitbit->initSession(CALLBACK_URL);

$profile = $fitbit->getProfile();

// Demo retrieval functionality by fetching today's step count
$today = date("Y-m-d");
$xml = $fitbit->getTimeSeries('steps', $today, '1d');
$steps = $xml[0]->value;

$results = 'For today, %s, %s took %s steps.';
echo sprintf($results, $today, $profile->user->fullName, $steps);

?>