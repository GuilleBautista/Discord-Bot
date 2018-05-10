package myBot;

import java.util.ArrayList;
import java.util.List;

import net.dv8tion.jda.core.events.guild.voice.GuildVoiceJoinEvent;
import net.dv8tion.jda.core.events.guild.voice.GuildVoiceLeaveEvent;
import net.dv8tion.jda.core.hooks.ListenerAdapter;

public class VoiceListener extends ListenerAdapter{
	
	List<String> connected=new ArrayList<String>();
	
	@Override
	public void onGuildVoiceJoin(GuildVoiceJoinEvent event) {
		
		String [] arr= {
				"Hola %s, te estábamos esperando :D",
		};
		String msg;
		if(connected.isEmpty())msg="Hoola %s, estamos solos y ya sabes lo que significa eeee";
		else msg=arr[(int)Math.random()*arr.length];
		
		connected.add(event.getMember().getUser().getName());
		
		event.getGuild().getTextChannels().get(1).sendMessageFormat(
				msg,
				event.getMember().getUser().getName()
				).queue();
	}
	
	@Override
	public void onGuildVoiceLeave(GuildVoiceLeaveEvent event) {
		String [] arr= {
				"Adios %s te echaremos de menos :(",
				"Aaaaaaaaaalgo se muere en el aaaaalmaaaaaaaa cuando un amigo se vaaaaaaaa (%s te queremos)",
				"Recuerda %s que para los cabreos siempre tendremos lejía ;)",
				
		};
		String msg=arr[(int)Math.random()*arr.length];
		
		connected.remove(event.getMember().getUser().getName());
		
		event.getGuild().getTextChannels().get(1).sendMessageFormat(
				msg,
				event.getMember().getUser().getName()
				).queue();
		
		if(connected.size()==1)
			event.getGuild().getTextChannels().get(1).sendMessageFormat(
					"Vaya, nos han dejado solos %s",
					connected.get(0)
					).queue();
		
	}
	
}
