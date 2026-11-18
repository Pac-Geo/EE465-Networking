% Paste into your ThingSpeak MATLAB Visualization editor.
readChannelID = 3585180;
readAPIKey = 'YOUR_READ_API_KEY';

% Field 1 = CPU temperature in degrees Celsius.
% Field 2 = overall CPU usage in percent (0 to 100).
[data,time] = thingSpeakRead(readChannelID, ...
    'Fields', [1,2], 'NumPoints', 20, 'ReadKey', readAPIKey);

if isempty(data)
    error('No data available. Run PorjB.py and confirm a successful upload.');
end

Temp_in_C = data(:,1);
CPU_percent = data(:,2);

% Assignment formula: 02.3 is interpreted as 2.3.
% CPU_percent remains on the 0-100 scale; it is not divided by 100.
POWER_in_W = 2.3 .* 100 .* CPU_percent + Temp_in_C .* 0.32;

plot(time,POWER_in_W,'r','LineWidth',2);
xlabel('Date and Time');
ylabel('Calculated Power (W)');
title('Raspberry Pi Power - Assignment Formula');
grid on;
