package myBot;

import net.dv8tion.jda.core.events.guild.voice.GuildVoiceJoinEvent;
import net.dv8tion.jda.core.events.guild.voice.GuildVoiceLeaveEvent;
import net.dv8tion.jda.core.hooks.ListenerAdapter;

public class VoiceListener extends ListenerAdapter{
	
	@Override
	public void onGuildVoiceJoin(GuildVoiceJoinEvent event) {
		event.getGuild().getTextChannels().get(0).sendMessageFormat(
				"Hola %s, te estábamos esperando :D",
				event.getMember().getUser().getName()
				).queue();
	}
	
	@Override
	public void onGuildVoiceLeave(GuildVoiceLeaveEvent event) {
		event.getGuild().getTextChannels().get(0).sendMessageFormat(
				"Adios %s te echaremos de menos :(",
				event.getMember().getUser().getName()
				).queue();
		
	}
	
}
