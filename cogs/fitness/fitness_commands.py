import decimal

from discord.ext import commands
from cogs.fitness.fitness_iface import FitnessUserInterface


class Fitness(commands.Cog):
    def __init__(self, casper):
        self.casper = casper

    @staticmethod
    async def calc_wilks(gender, bodyweight, bench, squat, dead):
        # test values
        bodyweight = decimal.Decimal('81.6466')
        total = decimal.Decimal('474.004')
        kg_constant = decimal.Decimal('2.205')
        x = bodyweight
        am = decimal.Decimal('-216.0475144')
        bm = decimal.Decimal('16.2606339')
        cm = decimal.Decimal('-0.002388645')
        dm = decimal.Decimal('-0.00113732')
        em = decimal.Decimal('0.00000701863')
        fm = decimal.Decimal('-0.00000001291')
        af = decimal.Decimal('594.31747775582')
        bf = decimal.Decimal('-27.23842536447')
        cf = decimal.Decimal('0.82112226871')
        df = decimal.Decimal('-0.00930733913')
        ef = decimal.Decimal('0.00004731582')
        ff = decimal.Decimal('-0.00000009054')
        coeff_m = 500 / (
            am + (bm * x) + (cm * (x ** 2)) + (dm * (x ** 3)) + (em * (x ** 4)) + (fm * (x ** 5))
        )
        coeff_f = 500 / (
            af + (bf * x) + (cf * (x ** 2)) + (df * (x ** 3)) + (ef * (x ** 4)) + (ff * (x ** 5))
        )
        return total * coeff_m

    @commands.command()
    async def setgender(self, ctx, gender):
        """
        Set your gender.
        :param ctx:
        :param gender:
        :return:
        """
        await FitnessUserInterface.setgender(ctx.author.name, ctx.guild.id, gender)
        output_str = await self.build_progress_msg(ctx)
        return await ctx.send(output_str)

    @commands.command()
    async def setheight(self, ctx, height):
        """
        Set your height.
        :param ctx:
        :param height:
        :return:
        """
        try:
            await FitnessUserInterface.setheight(ctx.author.name, ctx.guild.id, float(height))
            output_str = await self.build_progress_msg(ctx)
            return await ctx.send(output_str)
        except ValueError:
            return await ctx.send('Please enter your height in inches.')

    @commands.command()
    async def setweight(self, ctx, weight):
        """
        Set how much you weigh.
        :param ctx:
        :param weight:
        :return:
        """
        try:
            await FitnessUserInterface.setweight(ctx.author.name, ctx.guild.id, float(weight))
            output_str = await self.build_progress_msg(ctx)
            return await ctx.send(output_str)
        except ValueError:
            return await ctx.send('Please enter your weight in pounds.')

    @commands.command()
    async def setgoalweight(self, ctx, weight):
        """
        Set your goal weight.
        :param ctx:
        :param weight:
        :return:
        """
        try:
            await FitnessUserInterface.setgoalweight(ctx.author.name, ctx.guild.id, float(weight))
            output_str = await self.build_progress_msg(ctx)
            return await ctx.send(output_str)
        except ValueError:
            return await ctx.send('Please enter your weight in pounds.')

    @commands.command()
    async def setbench(self, ctx, weight):
        """
        Set how much you bench.
        :param ctx:
        :param weight:
        :return:
        """
        try:
            await FitnessUserInterface.setbench(ctx.author.name, ctx.guild.id, float(weight))
            output_str = await self.build_progress_msg(ctx)
            return await ctx.send(output_str)
        except ValueError:
            return await ctx.send('Please enter your weight in pounds.')

    @commands.command()
    async def setsquat(self, ctx, weight):
        """
        Set how much you back squat.
        :param ctx:
        :param weight:
        :return:
        """
        try:
            await FitnessUserInterface.setsquat(ctx.author.name, ctx.guild.id, float(weight))
            output_str = await self.build_progress_msg(ctx)
            return await ctx.send(output_str)
        except ValueError:
            return await ctx.send('Please enter your weight in pounds.')

    @commands.command()
    async def setdeadlift(self, ctx, weight):
        """
        Set how much you deadlift.
        :param ctx:
        :param weight:
        :return:
        """
        try:
            await FitnessUserInterface.setdeadlift(ctx.author.name, ctx.guild.id, float(weight))
            output_str = await self.build_progress_msg(ctx)
            return await ctx.send(output_str)
        except ValueError:
            return await ctx.send('Please enter your weight in pounds.')

    @commands.command()
    async def setohp(self, ctx, weight):
        """
        Set how much you overhead press.
        :param ctx:
        :param weight:
        :return:
        """
        try:
            await FitnessUserInterface.setohp(ctx.author.name, ctx.guild.id, float(weight))
            output_str = await self.build_progress_msg(ctx)
            return await ctx.send(output_str)
        except ValueError:
            return await ctx.send('Please enter your weight in pounds.')

    @commands.command()
    async def setmile(self, ctx, time):
        """
        Set how fast you run your mile.
        :param ctx:
        :param time:
        :return:
        """
        if ':' not in time:
            return await ctx.send('Please enter your time as `M:SS`.')
        await FitnessUserInterface.setmile(ctx.author.name, ctx.guild.id, time)
        output_str = await self.build_progress_msg(ctx)
        return await ctx.send(output_str)

    @commands.command()
    async def setrowing(self, ctx, time):
        """
        Set how fast you can row 2,000 meters.
        :param ctx:
        :param time:
        :return:
        """
        if ':' not in time:
            return await ctx.send('Please enter your time as `M:SS`.')
        await FitnessUserInterface.setrowing(ctx.author.name, ctx.guild.id, time)
        output_str = await self.build_progress_msg(ctx)
        return await ctx.send(output_str)

    @commands.command()
    async def setburpees(self, ctx, count):
        """
        Set how many burpees you can do in 1 minute.
        :param ctx:
        :param count:
        :return:
        """
        try:
            await FitnessUserInterface.setburpees(ctx.author.name, ctx.guild.id, int(count))
            output_str = await self.build_progress_msg(ctx)
            return await ctx.send(output_str)
        except ValueError:
            return await ctx.send('Please enter the number of burpees as a whole number.')

    @commands.command()
    async def setplank(self, ctx, time):
        """
        Set how long you can hold a plank.
        :param ctx:
        :param time:
        :return:
        """
        if ':' not in time:
            return await ctx.send('Please enter your time as `M:SS`.')
        await FitnessUserInterface.setplank(ctx.author.name, ctx.guild.id, time)
        output_str = await self.build_progress_msg(ctx)
        return await ctx.send(output_str)

    @commands.command()
    async def progress(self, ctx):
        """Check the current progress of yourself, or someone else if you enter their
        name.
        """
        output_str = await self.build_progress_msg(ctx)
        return await ctx.send(output_str)

    @commands.command(hidden=True)
    async def leaderboards(self, ctx, sort=None):
        # TODO: Implement
        sort = sort.lower()
        if sort is None:
            return await ctx.send('How do you want to sort the leaderboard?\n'
                                  'Ex: `casper leaderboards weight`')
        if sort == 'height':
            ...
        elif sort == 'weight':
            ...
        elif sort == 'bench':
            ...
        elif sort == 'squat':
            ...
        elif sort == 'deadlift':
            ...
        elif sort == 'ohp':
            ...
        elif sort == 'mile':
            ...
        elif sort == 'burpees':
            ...
        elif sort == 'plank':
            ...
        else:
            return await ctx.send('Not a valid sort method.\n'
                                  '```height\nweight\nbench\nsquat\ndeadlift\n'
                                  'ohp\nmile\nburpees\nplank```')

    @staticmethod
    async def build_progress_msg(ctx):
        fitness_user = await FitnessUserInterface.get_progress(ctx.author.name, ctx.guild.id)
        output_str = f'**__Current Progress for {fitness_user.user.title()}:__**\n'
        output_str += (f'{fitness_user.gender.title()}\n'
                       f'{fitness_user.height} in.\n'
                       f'Current Weight: {fitness_user.weight} lbs\n'
                       f'Goal Weight: {fitness_user.goal_weight} lbs\n\n'
                       f'Bench: {fitness_user.bench_press} lbs **|** '
                       f'Squat: {fitness_user.back_squat} lbs **|** '
                       f'Deadlift: {fitness_user.deadlift} lbs **|** '
                       f'OHP: {fitness_user.ohp} lbs\n\n'
                       f'Mile Run Time: {fitness_user.mile} **|** '
                       f'2000 Meter Row Time: {fitness_user.row_2km}\n\n'
                       f'Burpees in 1 min: {fitness_user.burpess_1m} **|** '
                       f'Plank time: {fitness_user.plank}')
        return output_str


def setup(casper):
    casper.add_cog(Fitness(casper))